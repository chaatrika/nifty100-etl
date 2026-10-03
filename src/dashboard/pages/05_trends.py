import plotly.graph_objects as go
import streamlit as st

from utils.db import get_pl, get_ratios
from utils.ui import company_picker, note_years

st.title("Trend Analysis")
ticker = company_picker("trend")
if not ticker:
    st.stop()

METRICS = {"Revenue (Cr)": ("pl", "sales"), "Net profit (Cr)": ("pl", "net_profit"),
           "ROE %": ("fr", "return_on_equity_pct"), "ROCE %": ("fr", "return_on_capital_employed_pct"),
           "Net margin %": ("fr", "net_profit_margin_pct"), "Operating margin %": ("fr", "operating_profit_margin_pct"),
           "D/E": ("fr", "debt_to_equity"), "Free cash flow (Cr)": ("fr", "free_cash_flow_cr"),
           "EPS": ("fr", "earnings_per_share")}
chosen = st.multiselect("Metrics (up to 3)", list(METRICS), default=["Revenue (Cr)", "ROE %"], max_selections=3)
if not chosen:
    st.info("Pick at least one metric.")
    st.stop()

pl, fr = get_pl(ticker).tail(10), get_ratios(ticker).tail(10)
note_years(pl if len(pl) else fr)
fig = go.Figure()
layout, colors = {}, ["#1f77b4", "#d62728", "#2ca02c"]
for i, name in enumerate(chosen):
    src, col = METRICS[name]
    d = pl if src == "pl" else fr
    if d.empty or d[col].notna().sum() == 0:
        st.caption(f"{name}: no data for this company.")
        continue
    y = d[col].astype(float)
    yoy = y.pct_change(fill_method=None) * 100
    text = ["" if (p != p or p in (float("inf"), float("-inf"))) else f"{p:+.0f}%" for p in yoy]   # blank if no valid base
    axis = "y" if i == 0 else f"y{i + 1}"
    fig.add_trace(go.Scatter(x=d["fy"], y=y, name=name, mode="lines+markers+text", text=text, textposition="top center",
                             line=dict(color=colors[i]), yaxis=axis))
    key = "yaxis" if i == 0 else f"yaxis{i + 1}"
    layout[key] = dict(title=dict(text=name, font=dict(color=colors[i])), tickfont=dict(color=colors[i]),
                       **({} if i == 0 else dict(overlaying="y", side="right", showgrid=False)),
                       **({"anchor": "free", "position": 0.92} if i == 2 else {}))
fig.update_layout(height=500, margin=dict(t=30, b=20), xaxis=dict(type="category", domain=[0, 0.9 if len(chosen) > 2 else 1]), **layout)
st.plotly_chart(fig, width="stretch")
st.caption("Labels show the year-on-year % change (blank where the previous value is zero or missing).")
