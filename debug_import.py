import sys
import os
sys.path.append(os.getcwd())

print("Attempting to import ScraperManager...")
try:
    from src.scraper_manager import ScraperManager
    print("Success importing ScraperManager")
except Exception as e:
    print(f"Error importing ScraperManager: {e}")
    import traceback
    traceback.print_exc()

print("\nAttempting to import BaseConnector...")
try:
    from src.connectors.base_connector import BaseConnector
    print("Success importing BaseConnector")
except Exception as e:
    print(f"Error importing BaseConnector: {e}")
    import traceback
    traceback.print_exc()