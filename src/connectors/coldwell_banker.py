from typing import List, Generator
from playwright.sync_api import sync_playwright
from src.connectors.base_connector import BaseConnector
from src.models import Agent
from src.utils import normalize_phone, parse_name
from src.config import USER_AGENT
from loguru import logger
import time

class CBConnector(BaseConnector):
    def __init__(self, rate_limit: float = 1.0):
        super().__init__("ColdwellBanker", rate_limit)
        self.base_url = "https://www.coldwellbankerhomes.com"

    def scrape(self, towns: List[str], zips: List[str], max_pages: int) -> Generator[Agent, None, None]:
        if not towns:
            logger.warning("No towns provided for Coldwell Banker.")
            return
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()

            for town_input in towns:
                # Parse "Town, State" from input if available
                if "," not in town_input:
                    logger.warning(f"Skipping '{town_input}' for Coldwell Banker - missing state (e.g. 'Town, State').")
                    continue

                town_name, state_code = [part.strip() for part in town_input.split(",", 1)]
                town_slug = town_name.lower().replace(" ", "-")
                state_slug = state_code.lower()
                
                url = f"{self.base_url}/{state_slug}/{town_slug}/agents/"
                logger.info(f"Scraping Coldwell Banker URL: {url}")
                
                try:
                    page.goto(url, timeout=60000)
                    page.wait_for_timeout(2000) # Wait for load
                except Exception as e:
                    logger.error(f"Failed to load {url}: {e}")
                    continue

                # Pagination loop
                current_page = 1
                while current_page <= max_pages:
                    logger.info(f"Processing page {current_page} for {town_name}")
                    
                    # Find agent blocks
                    agent_blocks = page.locator('.agent-block')
                    count = agent_blocks.count()
                    logger.info(f"Found {count} agents on page {current_page}")
                    
                    if count == 0:
                        logger.warning("No agents found, stopping.")
                        break

                    # Collect basic info and profile URLs
                    page_agents = []
                    for i in range(count):
                        try:
                            block = agent_blocks.nth(i)
                            
                            # Name
                            name_el = block.locator('.agent-content-name a')
                            if name_el.count() == 0:
                                continue
                            full_name = name_el.text_content().strip()
                            profile_href = name_el.get_attribute("href")
                            profile_url = f"{self.base_url}{profile_href}" if profile_href else ""
                            
                            # Phone
                            phone_el = block.locator('a.phone-link')
                            phone = ""
                            if phone_el.count() > 0:
                                # Prefer mobile if available, otherwise take first
                                mobile_el = block.locator('a.phone-link[data-phone-type="mobile"]')
                                if mobile_el.count() > 0:
                                    phone = normalize_phone(mobile_el.first.text_content().strip())
                                else:
                                    phone = normalize_phone(phone_el.first.text_content().strip())
                                
                            # Office
                            office_el = block.locator('p.office a')
                            office = office_el.text_content().strip() if office_el.count() > 0 else ""
                            
                            first, last = parse_name(full_name)
                            
                            page_agents.append({
                                "first": first,
                                "last": last,
                                "full_name": full_name,
                                "phone": phone,
                                "office": office,
                                "profile_url": profile_url,
                                "town": town_name,
                                "state": state_code.upper()
                            })
                            
                        except Exception as e:
                            logger.error(f"Error parsing agent block {i}: {e}")

                    # Now visit each profile to get email
                    for agent_data in page_agents:
                        if not agent_data["profile_url"]:
                            continue
                            
                        try:
                            logger.info(f"Visiting profile: {agent_data['profile_url']}")
                            page.goto(agent_data["profile_url"], timeout=30000)
                            # page.wait_for_selector('a[href^="mailto:"]', timeout=5000) # Might not exist
                            
                            email = ""
                            email_el = page.locator('a[href^="mailto:"]')
                            if email_el.count() > 0:
                                href = email_el.first.get_attribute("href")
                                if href:
                                    email = href.replace("mailto:", "").split("?")[0].strip()
                            
                            agent = Agent(
                                first_name=agent_data["first"],
                                last_name=agent_data["last"],
                                full_name=agent_data["full_name"],
                                email=email,
                                phone=agent_data["phone"],
                                brokerage=f"Coldwell Banker - {agent_data['office']}",
                                city=agent_data["town"].title(),
                                state=agent_data["state"],
                                source="Coldwell Banker",
                                source_url=agent_data["profile_url"],
                                scraped_at=time.strftime("%Y-%m-%d %H:%M:%S")
                            )
                            yield agent
                            
                            self._sleep()
                            
                        except Exception as e:
                            logger.error(f"Error scraping profile {agent_data['profile_url']}: {e}")
                            # Yield partial data
                            agent = Agent(
                                first_name=agent_data["first"],
                                last_name=agent_data["last"],
                                full_name=agent_data["full_name"],
                                email="",
                                phone=agent_data["phone"],
                                brokerage=f"Coldwell Banker - {agent_data['office']}",
                                city=agent_data["town"].title(),
                                state=agent_data["state"],
                                source="Coldwell Banker",
                                source_url=agent_data["profile_url"],
                                scraped_at=time.strftime("%Y-%m-%d %H:%M:%S")
                            )
                            yield agent

                    # Go back to list page for next iteration if needed
                    # Actually, visiting profiles navigates away.
                    # We need to restore the list page state.
                    # Since we are iterating pages via URL, we can just goto the next page URL.
                    
                    current_page += 1
                    if current_page > max_pages:
                        break
                        
                    next_url = f"{self.base_url}/pa/{town_slug}/agents/p_{current_page}/"
                    logger.info(f"Moving to next page: {next_url}")
                    try:
                        page.goto(next_url, timeout=60000)
                        page.wait_for_timeout(2000)
                    except Exception as e:
                        logger.error(f"Failed to load next page {next_url}: {e}")
                        break
            
            browser.close()
