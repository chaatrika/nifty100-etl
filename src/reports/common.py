# common.py - colours, formatting and data helpers shared by the PDF reports (Sprint 5)
import os
import re
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
from reportlab.lib import colors

from src.analytics import series

NAVY = colors.HexColor("#1F3864")
GREEN = colors.HexColor("#2E7D32")
RED = colors.HexColor("#C62828")
GREY = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#F3F4F6")
PROS_CONS_CSV = os.path.join("output", "pros_cons_generated.csv")


def esc(text):
    return escape("" if text is None or (isinstance(text, float) and np.isnan(text)) else str(text))


def fmt(value, suffix="", decimals=1, prefix=""):
    try:
        if value is None or pd.isna(value) or np.isinf(value):
            return "N/A"
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def safe_name(text):
    # same rule as the radar chart file names: M&M -> M_M
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")


def load_bundle():
    # everything the reports need, loaded once
    data = series.load_all()
    bundle = {
        "companies": data["companies"].set_index("company_id"),
        "ratios": series.by_company(data["ratios"]),
        "pl": series.by_company(data["pl"]),
        "bs": series.by_company(data["bs"]),
        "cf": series.by_company(data["cf"]),
        "mc": {k: g.sort_values("year") for k, g in data["mc"].groupby("company_id")},
    }
    if os.path.exists(PROS_CONS_CSV):
        pc = pd.read_csv(PROS_CONS_CSV)
    else:
        from src.nlp.pros_cons_generator import generate
        pc = generate(data)
    bundle["pros_cons"] = {k: g for k, g in pc.groupby("company_id")}
    caps = os.path.join("output", "capital_allocation.csv")
    bundle["pattern"] = {}
    if os.path.exists(caps):
        p = series.annual(pd.read_csv(caps), "pattern_label").sort_values("fy").groupby("company_id").tail(1)
        bundle["pattern"] = dict(zip(p["company_id"], p["pattern_label"]))
    return bundle


def latest(df, col):
    if df is None or len(df) == 0 or col not in df:
        return np.nan
    s = df[col].dropna()
    return s.iloc[-1] if len(s) else np.nan
