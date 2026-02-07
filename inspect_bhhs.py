from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Add more headers to mimic a real browser request to bypass 403
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            extra_http_headers={
                "Referer": "https://wayne-devon.foxroach.com/roster/agents",
                "Origin": "https://wayne-devon.foxroach.com",
                "X-Requested-With": "XMLHttpRequest",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        
        # Check page 1 with larger page size
        page1 = context.new_page()
        url1 = "https://wayne-devon.foxroach.com/roster/agents?pagesize=100"
        # Log responses
        page1.on("response", lambda response: print(f"Response: {response.status} {response.url}") if response.status != 200 else None)
        
        print(f"Loading {url1}...")
        page1.goto(url1)
        page1.wait_for_timeout(5000)
        
        cards1 = page1.locator('article.rng-agent-roster-agent-card')
        count1 = cards1.count()
        print(f"Page 1 (pagesize=100) cards: {count1}")
        
        if count1 > 0:
            print("\n--- First Card HTML ---")
            print(cards1.first.inner_html())
            print("-----------------------\n")
        
        # Try Search
        print("Testing Search...")
        try:
            page1.fill("#agentRosterSearch", "Smith")
            page1.press("#agentRosterSearch", "Enter")
            page1.wait_for_timeout(5000)
            
            cards_search = page1.locator('article.rng-agent-roster-agent-card')
            print(f"Cards after searching 'Smith': {cards_search.count()}")
        except Exception as e:
            print(f"Search failed: {e}")
        
        browser.close()

if __name__ == "__main__":
    inspect()