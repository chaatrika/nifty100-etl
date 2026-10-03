import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import YEARS, get_universe
from utils.ui import fmt

st.title("Nifty 100 Analytics")
year = st.sidebar.selectbox("Financial year", YEARS[::-1], index=0)
df = get_universe(year)

if df.empty:
    st.warning("No data for this year.")
    st.stop()

# "debt free" = D/E of 0.1 or less (same rule as the Debt-Free Blue Chip screener preset)
debt_free = int((df["debt_to_equity"] <= 0.1).sum())
c = st.columns(6)
c[0].metric("Average ROE", fmt(df["return_on_equity_pct"].mean(), "%"),
            help=f"Simple average. Median is {fmt(df['return_on_equity_pct'].median(), '%')} - a few extreme ROE values pull the average up.")
c[1].metric("Median P/E (SIMULATED)", fmt(df["pe_ratio"].median()), help="P/E comes from the simulated market_cap table.")
c[2].metric("Median D/E", fmt(df["debt_to_equity"].median(), decimals=2))
c[3].metric("Total Companies", len(df), help="Companies with data for the selected year")
c[4].metric("Median Revenue CAGR 5yr", fmt(df["revenue_cagr_5yr"].median(), "%"))
c[5].metric("Debt-Free Companies", debt_free, help="D/E of 0.1 or less")

left, right = st.columns([1, 1])
with left:
    st.subheader("Companies by sector")
    sec = df["broad_sector"].fillna("Unclassified").value_counts().reset_index()
    sec.columns = ["sector", "companies"]
    fig = px.pie(sec, names="sector", values="companies", hole=0.5)
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=380)
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("Top 5 by composite quality score")
    top = df.sort_values("composite_quality_score", ascending=False).head(5)
    show = top[["company_id", "company_name", "broad_sector", "composite_quality_score"]].copy()
    show.columns = ["Ticker", "Company", "Sector", "Quality score"]
    show["Quality score"] = show["Quality score"].round(1)
    st.dataframe(show, hide_index=True, width="stretch")
    st.caption(f"Financial year {year}. Sectors found in the data: {sec.shape[0]}.")
