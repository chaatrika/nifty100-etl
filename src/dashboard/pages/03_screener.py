import streamlit as st

from src.screener import engine as E
from utils.db import get_screener_config, get_screener_universe
from utils.ui import fmt

st.title("Screener")
df, config = get_screener_universe(), get_screener_config()

# slider key -> (label, min, max, step, "off" value = the extreme end, meaning no filter)
SLIDERS = {
    "roe_min": ("ROE min (%)", -10.0, 60.0, 1.0, -10.0),
    "de_max": ("D/E max", 0.0, 10.0, 0.1, 10.0),
    "fcf_min": ("FCF min (Cr)", -10000.0, 100000.0, 500.0, -10000.0),
    "revenue_cagr_5yr_min": ("Revenue CAGR 5yr min (%)", -10.0, 40.0, 1.0, -10.0),
    "pat_cagr_5yr_min": ("PAT CAGR 5yr min (%)", -10.0, 60.0, 1.0, -10.0),
    "opm_min": ("OPM min (%)", -10.0, 80.0, 1.0, -10.0),
    "pe_max": ("P/E max (SIMULATED)", 0.0, 200.0, 1.0, 200.0),
    "pb_max": ("P/B max", 0.0, 30.0, 0.5, 30.0),
    "dividend_yield_min": ("Dividend yield min % (SIMULATED)", 0.0, 6.0, 0.1, 0.0),
    "icr_min": ("Interest coverage min", 0.0, 100.0, 1.0, 0.0),
}
PRESETS = {"Quality": "quality_compounder", "Value": "value_pick", "Growth": "growth_accelerator",
           "Dividend": "dividend_champion", "Debt-Free": "debt_free_blue_chip", "Turnaround": "turnaround_watch"}

for k, spec in SLIDERS.items():
    st.session_state.setdefault("s_" + k, spec[4])
st.session_state.setdefault("extra", {})
st.session_state.setdefault("exclude", [])
st.session_state.setdefault("preset_name", None)


def reset():
    for k, spec in SLIDERS.items():
        st.session_state["s_" + k] = spec[4]
    st.session_state.update(extra={}, exclude=[], preset_name=None)


def apply_preset(label):
    reset()
    p = config["presets"][PRESETS[label]]
    for k, v in p["filters"].items():
        if k in SLIDERS:
            lo, hi = SLIDERS[k][1], SLIDERS[k][2]
            st.session_state["s_" + k] = float(min(max(v, lo), hi))
        else:
            st.session_state["extra"][k] = v      # filters that have no slider
    st.session_state["exclude"] = list(p.get("exclude_sectors") or [])
    st.session_state["preset_name"] = label


st.write("Presets (they fill the sliders):")
cols = st.columns(len(PRESETS) + 1)
for col, label in zip(cols, PRESETS):
    col.button(label, on_click=apply_preset, args=(label,), width="stretch")
cols[-1].button("Reset", on_click=reset, width="stretch")

st.sidebar.header("Filters")
filters = {}
for k, (label, lo, hi, step, off) in SLIDERS.items():
    val = st.sidebar.slider(label, lo, hi, step=step, key="s_" + k)
    if val != off:                      # sitting at the extreme end = filter is off
        filters[k] = val
filters.update(st.session_state["extra"])

if st.session_state["preset_name"]:
    extra = ", ".join(f"{k}={v}" for k, v in st.session_state["extra"].items())
    ex = ", ".join(st.session_state["exclude"])
    st.caption(f"Preset: {st.session_state['preset_name']}"
               + (f" | extra filters: {extra}" if extra else "") + (f" | excluding sectors: {ex}" if ex else ""))

res = E.apply_filters(df, filters, st.session_state["exclude"] or None)
st.subheader(f"{len(res)} companies match your filters")

COLUMN_OF = {**{k: v[0] for k, v in E.FILTERS.items()}, "fcf_positive_latest": "free_cash_flow_cr", "de_declining": "debt_to_equity"}
metric_cols = list(dict.fromkeys(COLUMN_OF[k] for k in filters))
show = res[["company_id", "company_name", "broad_sector", "composite_quality_score"] + metric_cols].copy()
show = show.rename(columns={"broad_sector": "sector", "composite_quality_score": "composite_score"})
show = show.round(2)

if show.empty:
    st.info("No company passes every filter. Loosen a slider or press Reset.")
else:
    st.dataframe(show, hide_index=True, width="stretch")
    st.download_button("Download CSV", show.to_csv(index=False).encode("utf-8"),
                       file_name="screener_results.csv", mime="text/csv")
st.caption("Data: latest year per company. A company with a missing value can't pass a filter on that value. "
           "Banks/NBFCs/insurers skip the D/E filter.")
