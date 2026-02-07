import pandas as pd
from typing import List, Dict
from src.models import Agent
from src.connectors.base_connector import BaseConnector
from src.connectors.compass import CompassConnector
from loguru import logger
import time
import os

class ScraperManager:
    def __init__(self, towns: List[str], zips: List[str], max_pages: int = 5, output_file: str = "contacts.csv"):
        self.towns = towns
        self.zips = zips
        self.max_pages = max_pages
        self.output_file = output_file
        self.connectors: List[BaseConnector] = []
        self.agents: List[Agent] = []
        
    def add_connector(self, connector: BaseConnector):
        self.connectors.append(connector)
        
    def run(self):
        logger.info(f"Starting scrape for {len(self.towns)} towns and {len(self.zips)} zips.")
        
        for connector in self.connectors:
            logger.info(f"Running connector: {connector.name}")
            try:
                for agent in connector.scrape(self.towns, self.zips, self.max_pages):
                    self.agents.append(agent)
                    logger.debug(f"Collected: {agent.full_name}")
            except Exception as e:
                logger.error(f"Connector {connector.name} failed: {e}")
                
        logger.info(f"Total raw agents collected: {len(self.agents)}")
        self.deduplicate()
        self.save_csv()
        
    def deduplicate(self):
        """Deduplicate agents based on email, phone, or name+brokerage."""
        unique_agents = []
        seen_emails = set()
        seen_phones = set()
        seen_names = set() # full_name + brokerage
        
        for agent in self.agents:
            # Key checks
            email_exists = agent.email and agent.email in seen_emails
            phone_exists = agent.phone and agent.phone in seen_phones
            name_key = f"{agent.full_name}|{agent.brokerage}"
            name_exists = name_key in seen_names
            
            if not (email_exists or phone_exists or name_exists):
                unique_agents.append(agent)
                if agent.email:
                    seen_emails.add(agent.email)
                if agent.phone:
                    seen_phones.add(agent.phone)
                seen_names.add(name_key)
            else:
                logger.debug(f"Duplicate filtered: {agent.full_name}")
                
        self.agents = unique_agents
        logger.info(f"Unique agents after deduplication: {len(self.agents)}")
        
    def save_csv(self):
        if not self.agents:
            logger.warning("No agents to save.")
            return
            
        df = pd.DataFrame([a.to_dict() for a in self.agents])
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else ".", exist_ok=True)
        
        df.to_csv(self.output_file, index=False)
        logger.info(f"Saved {len(df)} agents to {self.output_file}")
