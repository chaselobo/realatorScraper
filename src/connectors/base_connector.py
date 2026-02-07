from abc import ABC, abstractmethod
from typing import List, Generator
from src.models import Agent
from loguru import logger
import time
import random

class BaseConnector(ABC):
    def __init__(self, name: str, rate_limit: float = 1.0):
        self.name = name
        self.rate_limit = rate_limit
    
    @abstractmethod
    def scrape(self, towns: List[str], zips: List[str], max_pages: int) -> Generator[Agent, None, None]:
        """Yields Agent objects."""
        pass

    def _sleep(self):
        """Sleep to respect rate limit with some jitter."""
        sleep_time = self.rate_limit + random.uniform(0, 0.5)
        time.sleep(sleep_time)
