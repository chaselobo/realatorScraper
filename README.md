# Real Estate Agent Scraper - Philadelphia Main Line

A lead-generation scraper app that collects real estate agent contact information for the Philadelphia Main Line area near Villanova.

## Features

- Scrapes agent data (Name, Email, Phone, Brokerage, etc.)
- Modular connector system (Compass, Generic Brokerage)
- CLI and Streamlit UI interfaces
- Data deduplication and normalization
- Configurable rate limiting and concurrency
- Export to CSV

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   python3 -m playwright install chromium
   ```

## Usage

### CLI

```bash
python main.py --area "Main Line" --max_pages 5 --out contacts.csv
```

### UI

```bash
python3 -m streamlit run app.py
```

## adding Connectors

See `src/connectors/README.md` (to be created) for instructions on adding new source connectors.
