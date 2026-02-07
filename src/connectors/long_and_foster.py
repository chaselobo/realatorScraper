from typing import List, Generator
from playwright.sync_api import sync_playwright
from src.connectors.base_connector import BaseConnector
from src.models import Agent
from src.utils import normalize_phone, parse_name
from src.config import USER_AGENT
from loguru import logger
import time
from datetime import datetime

class LongAndFosterConnector(BaseConnector):
    def __init__(self, rate_limit: float = 1.0):
        super().__init__("LongAndFoster", rate_limit)
        self.base_url = "https://www.longandfoster.com/Office/LongandFosterWayneDevonPARealty-102522"

    def scrape(self, towns: List[str], zips: List[str], max_pages: int) -> Generator[Agent, None, None]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()

            logger.info(f"Scraping Long & Foster URL: {self.base_url}")
            try:
                page.goto(self.base_url, timeout=60000)
                page.wait_for_timeout(3000) # Allow carousel to init
            except Exception as e:
                logger.error(f"Failed to load {self.base_url}: {e}")
                return

            agent_profiles = set()
            
            # Using the specific selector from inspection
            cards = page.locator('article.lf-roster-card.lf-agent')
            count = cards.count()
            logger.info(f"Found {count} L&F agent cards (raw)")
            
            profiles_to_visit = []
            
            for i in range(count):
                card = cards.nth(i)
                try:
                    name_link = card.locator('a.lf-h5-alt').first
                    if name_link.count() == 0:
                        continue
                        
                    full_name = name_link.inner_text().strip()
                    href = name_link.get_attribute('href')
                    
                    if not href or href in agent_profiles:
                        continue
                        
                    agent_profiles.add(href)
                    
                    profile_url = f"https://www.longandfoster.com{href}" if href.startswith('/') else href
                    
                    profiles_to_visit.append({
                        "full_name": full_name,
                        "profile_url": profile_url
                    })
                    
                except Exception as e:
                    continue
            
            logger.info(f"Found {len(profiles_to_visit)} unique L&F agents. Visiting profiles...")
            
            for p_data in profiles_to_visit:
                try:
                    time.sleep(self.rate_limit)
                    
                    p_url = p_data['profile_url']
                    logger.info(f"Visiting {p_url}")
                    page.goto(p_url, timeout=30000)
                    
                    phone_el = page.locator('a[href^="tel:"]').first
                    phone = None
                    if phone_el.count() > 0:
                        phone_href = phone_el.get_attribute('href')
                        phone = normalize_phone(phone_href.replace('tel:', ''))
                    
                    email_el = page.locator('a[href^="mailto:"]').first
                    email = None
                    if email_el.count() > 0:
                        email_href = email_el.get_attribute('href')
                        email = email_href.replace('mailto:', '').split('?')[0]
                    
                    first, last = parse_name(p_data['full_name'])
                    
                    agent = Agent(
                        first_name=first,
                        last_name=last,
                        full_name=p_data['full_name'],
                        email=email,
                        phone=phone,
                        brokerage="Long & Foster",
                        city="Wayne", 
                        state="",
                        zip_code="19087",
                        source=self.name,
                        source_url=p_url,
                        scraped_at=datetime.now().isoformat()
                    )
                    yield agent
                    
                except Exception as e:
                    logger.warning(f"Error scraping profile {p_data['profile_url']}: {e}")
                    continue