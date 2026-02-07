from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        # New URL from search results
        url = "https://www.longandfoster.com/Office/LongandFosterWayneDevonPARealty-102522"
        
        print(f"Loading {url}...")
        page = context.new_page()
        page.goto(url)
        page.wait_for_timeout(5000)
        
        print(f"Current URL: {page.url}")
        
        # Save HTML
        with open("lf_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("Saved HTML to lf_dump.html")
        
        # Try to find agent cards
        # Look for typical patterns
        cards = page.locator('article')
        print(f"Found {cards.count()} 'article' elements")
        
        browser.close()

if __name__ == "__main__":
    inspect()