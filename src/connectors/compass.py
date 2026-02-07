from typing import List, Generator
from playwright.sync_api import sync_playwright
from src.connectors.base_connector import BaseConnector
from src.models import Agent
from src.utils import normalize_phone, parse_name
from src.config import USER_AGENT
from loguru import logger
import time

class CompassConnector(BaseConnector):
    def __init__(self, rate_limit: float = 1.0):
        super().__init__("Compass", rate_limit)
        # Main Line and Philadelphia URLs
        self.start_urls = [
            "https://www.compass.com/agents/locations/main-line-bryn-mawr-pa/15715/",
            "https://www.compass.com/agents/locations/philadelphia-pa/14527/"
        ]

    def scrape(self, towns: List[str], zips: List[str], max_pages: int) -> Generator[Agent, None, None]:
        # Determine URLs to scrape
        urls = []
        
        # Try to generate dynamic URLs from input
        for town_input in towns:
            if "," in town_input:
                town, state = [x.strip() for x in town_input.split(",", 1)]
                # Pattern: https://www.compass.com/agents/locations/ridgewood-nj/
                slug = f"{town.lower().replace(' ', '-')}-{state.lower()}"
                urls.append(f"https://www.compass.com/agents/locations/{slug}/")
        
        # If no dynamic URLs (or only plain towns provided), use defaults if it looks like Main Line request,
        # otherwise warn.
        if not urls:
            logger.info("No 'Town, State' inputs found. Using default Main Line URLs.")
            urls = self.start_urls
        else:
            logger.info(f"Generated dynamic Compass URLs: {urls}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()

            for url in urls:
                logger.info(f"Scraping Compass URL: {url}")
                try:
                    page.goto(url, timeout=60000)
                    # Check for 404 or redirect to home
                    if page.url == "https://www.compass.com/" or "404" in page.title():
                        logger.warning(f"URL {url} redirected to home or 404. Skipping.")
                        continue
                        
                    page.wait_for_selector('[class*="agentCard"]', timeout=10000)
                except Exception as e:
                    logger.error(f"Failed to load {url}: {e}")
                    continue

                # Scroll to load more agents
                # We treat each scroll as a "page" roughly
                previous_count = 0
                for i in range(max_pages):
                    cards = page.locator('[class*="agentCard"]')
                    count = cards.count()
                    logger.info(f"Found {count} agents so far...")
                    
                    if count == previous_count and i > 0:
                        logger.info("No new agents loaded, stopping scroll.")
                        break
                    
                    previous_count = count
                    
                    # Scroll to bottom
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    self._sleep() # Wait for load
                    
                    # Yield new agents (or all and dedupe later)
                    # For simplicity, we parse all at the end or parse visible ones.
                    # Since DOM elements might be removed/added, parsing all at the end is safer if memory allows,
                    # but for large lists, we might want to parse incrementally.
                    # However, Playwright handles locators dynamically.
                    
                # Parse all visible cards
                cards = page.locator('[class*="agentCard"]')
                count = cards.count()
                logger.info(f"Parsing {count} agents from {url}")
                
                for i in range(count):
                    try:
                        card = cards.nth(i)
                        
                        # Extract Name
                        name_el = card.locator('.agentCard-name')
                        if name_el.count() == 0:
                            continue
                        full_name = name_el.text_content().strip()
                        first, last = parse_name(full_name)
                        
                        # Extract Email
                        email_el = card.locator('a[href^="mailto:"]')
                        email = ""
                        if email_el.count() > 0:
                            href = email_el.get_attribute("href")
                            if href:
                                email = href.replace("mailto:", "").strip()
                        
                        # Extract Phone
                        phone_el = card.locator('a[href^="tel:"]')
                        phone = ""
                        if phone_el.count() > 0:
                            phone_text = phone_el.text_content().strip()
                            # Often text is "M: 215..."
                            phone = normalize_phone(phone_text)
                        
                        # Extract Link
                        link_el = card.locator('a.agentCard-imageWrapper')
                        source_url = ""
                        if link_el.count() > 0:
                            href = link_el.get_attribute("href")
                            if href:
                                source_url = f"https://www.compass.com{href}"
                        
                        agent = Agent(
                            first_name=first,
                            last_name=last,
                            full_name=full_name,
                            email=email,
                            phone=phone,
                            brokerage="Compass",
                            source="Compass",
                            source_url=source_url,
                            scraped_at=time.strftime("%Y-%m-%dT%H:%M:%S")
                        )
                        
                        # Filter by town/zip if possible? 
                        # Since we are scraping a "Main Line" page, we assume they serve the area.
                        # We can refine later if we visit profile pages.
                        
                        yield agent
                        
                    except Exception as e:
                        logger.error(f"Error parsing card {i}: {e}")
            
            browser.close()
