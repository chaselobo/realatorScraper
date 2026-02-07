from typing import List, Generator
from playwright.sync_api import sync_playwright
from src.connectors.base_connector import BaseConnector
from src.models import Agent
from src.utils import normalize_phone, parse_name
from src.config import USER_AGENT
from loguru import logger
import time
from datetime import datetime

class BHHSConnector(BaseConnector):
    def __init__(self, rate_limit: float = 1.0):
        super().__init__("BHHS", rate_limit)
        # Using the specific Wayne-Devon office URL as requested/inspected
        self.base_url = "https://wayne-devon.foxroach.com/roster/agents"

    def scrape(self, towns: List[str], zips: List[str], max_pages: int) -> Generator[Agent, None, None]:
        url = f"{self.base_url}?pagesize=100"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()

            logger.info(f"Scraping BHHS URL: {url}")
            try:
                page.goto(url, timeout=60000)
                page.wait_for_timeout(2000)
            except Exception as e:
                logger.error(f"Failed to load {url}: {e}")
                return

            cards = page.locator('div.rn-agent-roster-card')
            count = cards.count()
            logger.info(f"Found {count} BHHS agents")
            
            for i in range(count):
                card = cards.nth(i)
                try:
                    # Name extraction
                    name_el = card.locator('h1.rn-agent-roster-name')
                    full_name_text = name_el.inner_text().strip()
                    
                    # Remove title if present (e.g., "Karen Teran Sales Associate")
                    title_el = card.locator('h1.rn-agent-roster-name span.account-title')
                    if title_el.count() > 0:
                        title_text = title_el.inner_text()
                        full_name = full_name_text.replace(title_text, "").strip()
                    else:
                        full_name = full_name_text
                    
                    first, last = parse_name(full_name)
                    
                    # Phone
                    phone_el = card.locator('a[href^="tel:"]').first
                    phone = None
                    if phone_el.count() > 0:
                        phone_href = phone_el.get_attribute('href')
                        phone = normalize_phone(phone_href.replace('tel:', ''))
                    
                    # Profile URL
                    profile_link = card.locator('div.rn-agent-roster-header a').first
                    profile_url = None
                    if profile_link.count() > 0:
                        href = profile_link.get_attribute('href')
                        if href:
                            profile_url = f"https://wayne-devon.foxroach.com{href}" if href.startswith('/') else href

                    agent = Agent(
                        first_name=first,
                        last_name=last,
                        full_name=full_name,
                        email=None, # No direct email on roster
                        phone=phone,
                        brokerage="BHHS Fox & Roach",
                        city="Wayne", 
                        state="PA",
                        zip_code="19087",
                        source=self.name,
                        source_url=profile_url or url,
                        scraped_at=datetime.now().isoformat()
                    )
                    yield agent
                    
                except Exception as e:
                    logger.warning(f"Error parsing BHHS agent card {i}: {e}")
                    continue