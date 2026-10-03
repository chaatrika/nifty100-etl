import plotly.express as px
import streamlit as st

from utils.db import YEARS, get_universe

st.title("Sector Analysis")
year = st.sidebar.selectbox("Financial year", YEARS[::-1])
df = get_universe(year)
sector = st.selectbox("Sector", sorted(df["broad_sector"].dropna().unique()))
d = df[df["broad_sector"] == sector].copy()
st.caption(f"{len(d)} companies in {sector}, financial year {year}.")

b = d.dropna(subset=["sales_cr", "return_on_equity_pct", "market_cap_crore"])
if b.empty:
    st.info("Not enough data for the bubble chart.")
else:
    lo, hi = b["return_on_equity_pct"].quantile([0.02, 0.98])
    pad = (hi - lo) * 0.15 or 5
    fig = px.scatter(b, x="sales_cr", y="return_on_equity_pct", size="market_cap_crore", color="sub_sector",
                     hover_name="company_name", size_max=55, labels={"sales_cr": "Revenue (Cr)", "return_on_equity_pct": "ROE %"})
    fig.update_yaxes(range=[min(lo - pad, 0), hi + pad])
    fig.update_layout(height=470, margin=dict(t=20, b=20))
    st.plotly_chart(fig, width="stretch")
    off = int(((b["return_on_equity_pct"] > hi + pad) | (b["return_on_equity_pct"] < min(lo - pad, 0))).sum())
    if off:
        st.caption(f"{off} company(ies) with extreme ROE are outside the chart range. Bubble size = market cap (SIMULATED).")
    else:
        st.caption("Bubble size = market cap (SIMULATED).")

st.subheader(f"{sector}: median KPIs")
cols = {"return_on_equity_pct": "ROE %", "return_on_capital_employed_pct": "ROCE %", "net_profit_margin_pct": "Net margin %",
        "operating_profit_margin_pct": "OPM %", "revenue_cagr_5yr": "Rev CAGR 5yr %", "pat_cagr_5yr": "PAT CAGR 5yr %",
        "debt_to_equity": "D/E", "pe_ratio": "P/E (SIMULATED)"}
med = d[list(cols)].median().rename(index=cols).reset_index()
med.columns = ["KPI", "Median"]
fig = px.bar(med, x="KPI", y="Median", text=med["Median"].round(1))
fig.update_layout(height=380, margin=dict(t=20, b=20))
st.plotly_chart(fig, width="stretch")
