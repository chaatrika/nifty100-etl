# ui.py - small helpers shared by the screens (N/A formatting, company search box)
import numpy as np
import pandas as pd
import streamlit as st

from utils.db import get_companies


def fmt(value, suffix="", decimals=1, prefix=""):
    # any missing value shows N/A instead of crashing
    try:
        if value is None or pd.isna(value) or np.isinf(value):
            return "N/A"
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def company_picker(key, default="TCS", label="Search company name or ticker"):
    # text box -> matching companies -> dropdown. Returns a company_id or None.
    companies = get_companies()
    query = st.text_input(label, value=default, key=key + "_q", placeholder="e.g. TCS or Infosys").strip()
    if not query:
        st.info("Type a company name or ticker to start.")
        return None
    q = query.lower()
    hits = companies[companies["company_id"].str.lower().str.contains(q, regex=False)
                     | companies["company_name"].str.lower().str.contains(q, regex=False)]
    if hits.empty:
        st.warning("Ticker not found — please try another")
        return None
    exact = hits[hits["company_id"].str.lower() == q]
    if len(hits) == 1 or (len(exact) == 1 and len(hits) == 1):
        return hits.iloc[0]["company_id"]
    labels = {r.company_id: f"{r.company_id} — {r.company_name}" for r in hits.itertuples()}
    ids = list(labels)
    index = ids.index(exact.iloc[0]["company_id"]) if len(exact) else 0
    return st.selectbox("Matches", ids, index=index, format_func=labels.get, key=key + "_sel")


SIMULATED_NOTE = ("SIMULATED DATA: stock_prices and market_cap (market cap, P/E, P/B, EV/EBITDA, dividend yield) "
                  "are simulated for this project and are not real market values.")


def simulated_note(short=False):
    # rule: simulated datasets must be clearly labelled as SIMULATED
    st.caption("SIMULATED market data (market cap, P/E, P/B, dividend yield)." if short else SIMULATED_NOTE)


def note_years(df, col="fy", target=10):
    if len(df) < target:
        st.caption(f"Data available for {len(df)} year(s) only (out of {target}).")
