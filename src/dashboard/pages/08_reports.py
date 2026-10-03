from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st

from utils.db import get_reports
from utils.ui import company_picker

st.title("Annual Reports")
ticker = company_picker("reports")
if not ticker:
    st.stop()

rep = get_reports(ticker)
if rep.empty:
    st.info("No annual report links for this company.")
    st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def check(url):
    # 404 / 410 -> unavailable, 2xx/3xx -> ok, anything else (403, timeout...) -> could not verify
    try:
        r = requests.head(url, timeout=5, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code in (404, 410):
            return "missing"
        return "ok" if r.status_code < 400 else "unknown"
    except requests.RequestException:
        return "unknown"


rep = rep[rep["annual_report"].notna() & (rep["annual_report"].str.strip() != "")]
st.write(f"{len(rep)} report link(s) found.")
verify = st.button("Check which links are still live")
status = {}
if verify:
    with st.spinner("Checking links..."), ThreadPoolExecutor(8) as ex:
        status = dict(zip(rep["annual_report"], ex.map(check, rep["annual_report"])))

for r in rep.itertuples():
    s = status.get(r.annual_report)
    badge = {"missing": " :red-background[Report unavailable]", "ok": " :green[✔ live]",
             "unknown": " :gray[could not verify]"}.get(s, "")
    st.markdown(f"**{r.year}** — [Open BSE PDF]({r.annual_report}){badge}")
