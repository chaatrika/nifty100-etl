import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils.db import get_companies, get_pl, get_pros_cons, get_ratios, get_valuation
from utils.ui import company_picker, fmt, note_years

st.title("Company Profile")
ticker = company_picker("profile")
if not ticker:
    st.stop()

info = get_companies().set_index("company_id").loc[ticker]
ratios, pl = get_ratios(ticker), get_pl(ticker)

st.subheader(f"{info['company_name']}  ({ticker})")
st.write(f"**Sector:** {info['broad_sector'] or 'N/A'}  |  **Sub-sector:** {info['sub_sector'] or 'N/A'}  |  **NSE ticker:** {ticker}")
st.write(info["about_company"] if isinstance(info["about_company"], str) and info["about_company"] else "No description available.")

latest = ratios.iloc[-1] if len(ratios) else None
g = (lambda k: latest[k] if latest is not None else None)
c = st.columns(6)
c[0].metric("ROE", fmt(g("return_on_equity_pct"), "%"))
c[1].metric("ROCE", fmt(g("return_on_capital_employed_pct"), "%"))
c[2].metric("Net Profit Margin", fmt(g("net_profit_margin_pct"), "%"))
c[3].metric("D/E", fmt(g("debt_to_equity"), decimals=2))
c[4].metric("Revenue CAGR 5yr", fmt(g("revenue_cagr_5yr"), "%"))
c[5].metric("FCF (latest, Cr)", fmt(g("free_cash_flow_cr"), decimals=0))
if latest is not None:
    st.caption(f"KPIs are for financial year {int(latest['fy'])}.")

val = get_valuation(ticker)
if len(val):
    v = val.iloc[0]
    st.caption(f"Valuation (SIMULATED market data): P/E {fmt(v['P/E'])} | FCF yield {fmt(v['FCF_yield_pct'], '%')} | flag: {v['flag']}")

pl10 = pl.tail(10)
note_years(pl10)
if len(pl10):
    a, b = st.columns(2)
    with a:
        fig = go.Figure()
        fig.add_bar(x=pl10["fy"], y=pl10["sales"], name="Revenue")
        fig.add_bar(x=pl10["fy"], y=pl10["net_profit"], name="Net profit")
        fig.update_layout(barmode="group", title="Revenue and Net Profit (Cr)", height=360, margin=dict(t=50, b=20))
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, width="stretch")
    with b:
        r10 = ratios.tail(10)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_scatter(x=r10["fy"], y=r10["return_on_equity_pct"], name="ROE %", mode="lines+markers")
        fig.add_scatter(x=r10["fy"], y=r10["return_on_capital_employed_pct"], name="ROCE %",
                        mode="lines+markers", secondary_y=True)
        fig.update_layout(title="ROE (left) and ROCE (right)", height=360, margin=dict(t=50, b=20))
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, width="stretch")
else:
    st.info("No profit and loss data available for this company.")

pc = get_pros_cons(ticker)
st.subheader("Pros and cons")
if pc.empty:
    st.caption("No pros/cons available for this company.")
else:
    p, q = st.columns(2)
    for row in pc.itertuples():
        if isinstance(row.pros, str) and row.pros:
            p.markdown(f":green[✅ {row.pros}]")
        if isinstance(row.cons, str) and row.cons:
            q.markdown(f":red[❌ {row.cons}]")
