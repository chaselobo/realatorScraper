from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Agent:
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    brokerage: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    areas_served: Optional[str] = None
    source: str = ""
    source_url: str = ""
    scraped_at: str = ""

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "brokerage": self.brokerage,
            "city": self.city,
            "state": self.state,
            "zip": self.zip_code,
            "areas_served": self.areas_served,
            "source": self.source,
            "source_url": self.source_url,
            "scraped_at": self.scraped_at
        }
