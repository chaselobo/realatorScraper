import pytest
import os
from playwright.sync_api import sync_playwright
from src.utils import normalize_phone

def test_compass_parsing():
    fixture_path = os.path.abspath("tests/fixtures/compass.html")
    url = f"file://{fixture_path}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Use the same loose selector
        cards = page.locator('[class*="agentCard"]')
        count = cards.count()
        
        extracted_agents = []
        
        for i in range(count):
            card = cards.nth(i)
            # Apply the logic from CompassConnector
            name_el = card.locator('.agentCard-name')
            if name_el.count() == 0:
                continue
            
            full_name = name_el.text_content().strip()
            
            # Extract Email
            email_el = card.locator('a[href^="mailto:"]')
            email = ""
            if email_el.count() > 0:
                email = email_el.get_attribute("href").replace("mailto:", "").strip()
            
            # Extract Phone
            phone_el = card.locator('a[href^="tel:"]')
            phone = ""
            if phone_el.count() > 0:
                phone = normalize_phone(phone_el.text_content().strip())
                
            extracted_agents.append({
                "name": full_name,
                "email": email,
                "phone": phone
            })
            
        # We expect at least one complete record for Jane Doe
        jane_records = [a for a in extracted_agents if a["name"] == "Jane Doe"]
        assert len(jane_records) >= 1
        
        # Check if any record has the correct email/phone
        jane_full = next((a for a in jane_records if a["email"] == "jane.doe@compass.com"), None)
        assert jane_full is not None
        assert jane_full["phone"] == "555-123-4567"
        
        # Check John Smith
        john_records = [a for a in extracted_agents if a["name"] == "John Smith"]
        assert len(john_records) >= 1
        assert john_records[0]["email"] == ""
        
        browser.close()
