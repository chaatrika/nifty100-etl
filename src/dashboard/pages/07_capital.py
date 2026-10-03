import plotly.express as px
import streamlit as st

from utils.db import get_capital_patterns

st.title("Capital Allocation Map")
df = get_capital_patterns()
if df.empty:
    st.warning("output/capital_allocation.csv not found. Run:  python -m src.analytics.run_ratio_engine")
    st.stop()

df["pattern_label"] = df["pattern_label"].fillna("Unknown")
fig = px.treemap(df.assign(all="All companies", n=1), path=["all", "pattern_label", "company_id"], values="n",
                 hover_data=["company_name"])
fig.update_layout(height=520, margin=dict(t=10, b=10, l=10, r=10))
st.plotly_chart(fig, width="stretch")
st.caption(f"{len(df)} companies, {df['pattern_label'].nunique()} patterns (latest year with a pattern for each company).")

counts = df["pattern_label"].value_counts()
pattern = st.selectbox("Show companies in pattern", list(counts.index), format_func=lambda p: f"{p} ({counts[p]})")
st.dataframe(df[df["pattern_label"] == pattern][["company_id", "company_name", "broad_sector", "year"]]
             .rename(columns={"year": "pattern year"}), hide_index=True, width="stretch")
