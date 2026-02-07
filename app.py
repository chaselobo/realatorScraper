import streamlit as st
import pandas as pd
from src.config import DEFAULT_TOWNS, DEFAULT_ZIPS, DEFAULT_MAX_PAGES
from src.scraper_manager import ScraperManager
from src.connectors.compass import CompassConnector
from src.connectors.coldwell_banker import CBConnector
from src.connectors.long_and_foster import LongAndFosterConnector
from src.connectors.bhhs import BHHSConnector
from src.utils import setup_logger
import time

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
    use_compass = st.checkbox("Compass", value=True)
    use_cb = st.checkbox("Coldwell Banker", value=True)
    use_lf = st.checkbox("Long & Foster", value=True)
    use_bhhs = st.checkbox("BHHS", value=True)
    
    output_file = st.text_input("Output Filename", "contacts.csv")
    
    run_btn = st.button("Run Scraper", type="primary")

if run_btn:
    towns = [t.strip() for t in towns_input.split(",")]
    zips = [z.strip() for z in zips_input.split(",")]
    
    st.info("Starting scraper... This may take a while.")
    
    # Capture logs? For now we just run it and show result.
    # To show live progress in Streamlit from internal logic is tricky without a callback or queue.
    # We'll just run it synchronously.
    
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
        
        st.success(f"Scraping completed! Found {len(manager.agents)} agents.")
        
        if manager.agents:
            df = pd.DataFrame([a.to_dict() for a in manager.agents])
            st.dataframe(df)
            
            with open(output_file, "rb") as f:
                st.download_button(
                    label="Download CSV",
                    data=f,
                    file_name=output_file,
                    mime="text/csv"
                )
        else:
            st.warning("No agents found.")
            
    except Exception as e:
        st.error(f"An error occurred: {e}")
