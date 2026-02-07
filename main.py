import argparse
from src.config import DEFAULT_TOWNS, DEFAULT_ZIPS, DEFAULT_MAX_PAGES
from src.scraper_manager import ScraperManager
from src.connectors.compass import CompassConnector
from src.connectors.coldwell_banker import CBConnector
from src.connectors.long_and_foster import LongAndFosterConnector
from src.connectors.bhhs import BHHSConnector
from src.utils import setup_logger

def main():
    parser = argparse.ArgumentParser(description="Real Estate Agent Scraper")
    parser.add_argument("--area", type=str, help="Area name (unused logic currently, uses towns)", default="Main Line")
    parser.add_argument("--towns", type=str, help="Comma-separated towns", default=",".join(DEFAULT_TOWNS))
    parser.add_argument("--zips", type=str, help="Comma-separated zip codes", default=",".join(DEFAULT_ZIPS))
    parser.add_argument("--max_pages", type=int, help="Max pages to scrape per source", default=DEFAULT_MAX_PAGES)
    parser.add_argument("--out", type=str, help="Output CSV file", default="contacts.csv")
    parser.add_argument("--sources", type=str, help="Comma-separated sources (compass, cb, lf, bhhs)", default="compass,cb,lf,bhhs")
    
    args = parser.parse_args()
    
    setup_logger()
    
    towns = [t.strip() for t in args.towns.split(",")]
    zips = [z.strip() for z in args.zips.split(",")]
    
    manager = ScraperManager(towns, zips, args.max_pages, args.out)
    
    sources = [s.strip().lower() for s in args.sources.split(",")]
    
    if "compass" in sources:
        manager.add_connector(CompassConnector())
        
    if "coldwellbanker" in sources or "cb" in sources:
        manager.add_connector(CBConnector())

    if "longandfoster" in sources or "lf" in sources:
        manager.add_connector(LongAndFosterConnector())

    if "bhhs" in sources:
        manager.add_connector(BHHSConnector())
        
    # Add other connectors here if implemented
    
    manager.run()

if __name__ == "__main__":
    main()
