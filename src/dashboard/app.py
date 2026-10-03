# app.py - Streamlit entry point (Sprint 4, Day 22)
# Run from the project root:   streamlit run src/dashboard/app.py
import streamlit as st

st.set_page_config(page_title="Nifty 100 Analytics", layout="wide", initial_sidebar_state="expanded")

pages = [
    st.Page("pages/01_home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/02_profile.py", title="Company Profile", icon="🏢"),
    st.Page("pages/03_screener.py", title="Screener", icon="🔎"),
    st.Page("pages/04_peers.py", title="Peer Comparison", icon="🆚"),
    st.Page("pages/05_trends.py", title="Trend Analysis", icon="📈"),
    st.Page("pages/06_sectors.py", title="Sector Analysis", icon="🧩"),
    st.Page("pages/07_capital.py", title="Capital Allocation", icon="💰"),
    st.Page("pages/08_reports.py", title="Annual Reports", icon="📄"),
]
# every screen carries the SIMULATED label (st.info, so page-level warnings stay first)
st.info("SIMULATED DATA: stock prices and market cap / P/E / P/B / dividend yield are simulated for this project.")
st.sidebar.caption("Market data is SIMULATED.")
st.navigation(pages).run()
