import streamlit as st
import pandas as pd
import subprocess
import os
from src.config import DEFAULT_TOWNS, DEFAULT_ZIPS, DEFAULT_MAX_PAGES

import sys

# Ensure Playwright browsers are installed
if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Failed to install Playwright browsers: {e}")

from src.scraper_manager import ScraperManager
from src.connectors.compass import CompassConnector
from src.connectors.coldwell_banker import CBConnector
from src.connectors.long_and_foster import LongAndFosterConnector
from src.connectors.bhhs import BHHSConnector
from src.utils import setup_logger
import time
from loguru import logger

# Initialize session state
if "results" not in st.session_state:
    st.session_state["results"] = None
if "logs" not in st.session_state:
    st.session_state["logs"] = []

st.set_page_config(page_title="Real Estate Agent Scraper", layout="wide")

st.title("🏡 JOJ Real Estate Agent Scraper")

with st.expander("ℹ️ How to Use & ChatGPT Prompt Helper"):
    st.markdown("""
    ### How to Use
    1. **Configure Area**: Update the **Towns** and **Zip Codes** in the sidebar to match your target market.
    2. **Select Sources**: Choose which brokerages to scrape (Compass, Coldwell Banker, etc.).
    3. **Run**: Click **Run Scraper** and wait for the process to complete.
    4. **Download**: Once finished, download the `contacts.csv` file with the results.

    ### 🤖 ChatGPT Prompt for Towns/Zips
    Use this prompt to easily generate the lists for the sidebar:
    > "I need a list of towns and their zip codes for **[Insert Area/County Name]**. 
    > Please provide two separate comma-separated lists:
    > 1. A list of just the town names.
    > 2. A list of just the zip codes."
    """)

with st.sidebar:
    st.header("Configuration")
    
    towns_input = st.text_area("Towns (comma-separated)", ", ".join(DEFAULT_TOWNS))
    zips_input = st.text_area("Zip Codes (comma-separated)", ", ".join(DEFAULT_ZIPS))
    
    max_pages = st.number_input("Max Pages per Source", min_value=1, max_value=1000, value=DEFAULT_MAX_PAGES)
    
    st.subheader("Sources")
    st.info("ℹ️ **Dynamic Search:** Connectors will search based on your 'Town, State' input. No default results are provided.")
    use_compass = st.checkbox("Compass", value=True)
    use_cb = st.checkbox("Coldwell Banker", value=True)
    use_lf = st.checkbox("Long & Foster", value=True)
    use_bhhs = st.checkbox("BHHS", value=True)
    
    output_file = st.text_input("Output Filename", "contacts.csv")
    
    run_btn = st.button("Run Scraper", type="primary")
    
    st.caption("Note: To stop the scraping process, use the 'Stop' button in the top-right corner of the app.")

# Log Display Area
st.subheader("📋 Progress Logs")
log_placeholder = st.empty()

if st.session_state["logs"]:
    log_placeholder.code("".join(st.session_state["logs"][-20:]))

if run_btn:
    # Clear previous state
    st.session_state["logs"] = []
    st.session_state["results"] = None
    
    towns = [t.strip() for t in towns_input.split(",")]
    zips = [z.strip() for z in zips_input.split(",")]
    
    # Validation
    if any("," not in t for t in towns) and any(use_cb, use_compass):
        st.warning("⚠️ Some towns are missing state codes (e.g., 'Ridgewood, NJ'). defaulting to PA for those entries.")

    # Define custom sink for Streamlit
    def streamlit_sink(message):
        st.session_state["logs"].append(message)
        log_placeholder.code("".join(st.session_state["logs"][-20:]))

    # Reset logger to output to our custom sink
    logger.remove()
    logger.add(streamlit_sink, format="{time:HH:mm:ss} | {level} | {message}")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    manager = ScraperManager(towns, zips, max_pages, output_file)
    
    if use_compass:
        manager.add_connector(CompassConnector())
        
    if use_cb:
        manager.add_connector(CBConnector())

    if use_lf:
        manager.add_connector(LongAndFosterConnector())

    if use_bhhs:
        manager.add_connector(BHHSConnector())
        
    try:
        status_text.text("Scraping in progress...")
        manager.run() # This blocks
        progress_bar.progress(100)
        status_text.text("Done!")
        
        if manager.agents:
            df = pd.DataFrame([a.to_dict() for a in manager.agents])
            st.session_state["results"] = df
            st.success(f"Scraping completed! Found {len(manager.agents)} agents.")
        else:
            st.warning("No agents found.")
            
    except Exception as e:
        st.error(f"An error occurred: {e}")
        logger.error(f"Error: {e}")

# Persistent Results & Download Section
if st.session_state["results"] is not None:
    st.divider()
    st.subheader("✅ Results")
    st.dataframe(st.session_state["results"])
    
    csv = st.session_state["results"].to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=output_file,
        mime="text/csv",
        key="download-csv"
    )
