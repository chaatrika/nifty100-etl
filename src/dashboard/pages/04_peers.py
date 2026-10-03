import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.db import get_peer_group_names, get_peer_percentiles, get_peers, get_universe
from utils.ui import fmt

st.title("Peer Comparison")
groups = get_peer_group_names()
group = st.selectbox("Peer group", groups)
peers = get_peers(group)
pp = get_peer_percentiles(group)

# 8 metrics for the radar (percentile rank inside the peer group, 0-100; D/E already flipped: higher = better)
RADAR = {"return_on_equity_pct": "ROE", "return_on_capital_employed_pct": "ROCE", "net_profit_margin_pct": "Net margin",
         "debt_to_equity": "D/E (low is good)", "free_cash_flow_cr": "FCF", "revenue_cagr_5yr": "Revenue CAGR 5yr",
         "pat_cagr_5yr": "PAT CAGR 5yr", "interest_coverage": "Interest cover"}

ids = peers["company_id"].tolist()
bench = peers.loc[peers["is_benchmark"] == 1, "company_id"].tolist()
label = {r.company_id: f"{r.company_id} — {r.company_name}" for r in peers.itertuples()}
company = st.selectbox("Company", ids, format_func=label.get, index=ids.index(bench[0]) if bench else 0)

if pp.empty:
    st.info("No peer percentile data for this group.")
else:
    year = int(pp["year"].max())
    d = pp[(pp["year"] == year) & (pp["metric"].isin(RADAR))]
    mine = d[d["company_id"] == company].set_index("metric")["percentile_rank"].reindex(RADAR).fillna(0)
    avg = d.groupby("metric")["percentile_rank"].mean().reindex(RADAR).fillna(0)
    names = list(RADAR.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=list(avg) + [avg.iloc[0]], theta=names + [names[0]], name="Peer group average", fill="toself", opacity=0.45))
    fig.add_trace(go.Scatterpolar(r=list(mine) + [mine.iloc[0]], theta=names + [names[0]], name=company, fill="toself", opacity=0.6))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=460, margin=dict(t=30, b=30),
                      title=f"Percentile rank inside {group} (year {year})")
    st.plotly_chart(fig, width="stretch")
    st.caption("Metrics with no value (e.g. interest cover for debt-free companies) are drawn as 0 on the radar.")

    # side-by-side KPI table
    yr_table = get_universe(year)
    tab = yr_table[yr_table["company_id"].isin(ids)].set_index("company_id").reindex(ids)
    cols = {"company_name": "Company", "return_on_equity_pct": "ROE %", "return_on_capital_employed_pct": "ROCE %",
            "net_profit_margin_pct": "Net margin %", "debt_to_equity": "D/E", "free_cash_flow_cr": "FCF (Cr)",
            "revenue_cagr_5yr": "Rev CAGR 5yr %", "pat_cagr_5yr": "PAT CAGR 5yr %", "pe_ratio": "P/E (SIMULATED)"}
    tab = tab[list(cols)].rename(columns=cols).round(2)
    tab.insert(0, "Benchmark", ["★" if i in bench else "" for i in tab.index])
    st.subheader("Peer KPI table")
    st.dataframe(tab.style.apply(lambda r: ["background-color: #fff3cd" if r["Benchmark"] else "" for _ in r], axis=1),
                 width="stretch")
