# db.py - shared cached data loader for the dashboard (Sprint 4, Day 22)
# Every query function is wrapped in @st.cache_data(ttl=600).
# Years: financial tables use strings like "2024-03". We turn them into a financial year
# number ("fy" = 2024) and keep the LAST row of each fy that has real data.

import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)          # so "from src...." imports work inside Streamlit

DB_PATH = os.path.join(ROOT, "data", "nifty100.db")
CAPITAL_CSV = os.path.join(ROOT, "output", "capital_allocation.csv")
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def _query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def _annual(df, key_col):
    # one row per company and financial year (last period of that year that has data)
    df = df[df[key_col].notna()].copy()
    df["fy"] = df["year"].str[:4].astype(int)
    return df.sort_values(["company_id", "year"]).groupby(["company_id", "fy"]).tail(1)


@st.cache_data(ttl=600)
def get_companies():
    return _query("SELECT c.id AS company_id, c.company_name, c.about_company, c.website, "
                  "s.broad_sector, s.sub_sector, s.market_cap_category "
                  "FROM companies c LEFT JOIN sectors s ON s.company_id = c.id ORDER BY c.id")


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    df = _annual(_query("SELECT * FROM financial_ratios WHERE company_id = ?", (ticker,)),
                 "net_profit_margin_pct")
    if year is not None:
        df = df[df["fy"] == int(year)]
    return df.sort_values("fy").reset_index(drop=True)


@st.cache_data(ttl=600)
def get_pl(ticker):
    return _annual(_query("SELECT * FROM profitandloss WHERE company_id = ?", (ticker,)),
                   "sales").sort_values("fy").reset_index(drop=True)


@st.cache_data(ttl=600)
def get_bs(ticker):
    return _annual(_query("SELECT * FROM balancesheet WHERE company_id = ?", (ticker,)),
                   "total_assets").sort_values("fy").reset_index(drop=True)


@st.cache_data(ttl=600)
def get_cf(ticker):
    return _annual(_query("SELECT * FROM cashflow WHERE company_id = ?", (ticker,)),
                   "operating_activity").sort_values("fy").reset_index(drop=True)


@st.cache_data(ttl=600)
def get_sectors():
    return _query("SELECT * FROM sectors ORDER BY broad_sector, company_id")


@st.cache_data(ttl=600)
def get_peer_group_names():
    return _query("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY 1")["peer_group_name"].tolist()


@st.cache_data(ttl=600)
def get_peers(group_name):
    return _query("SELECT p.company_id, c.company_name, p.is_benchmark FROM peer_groups p "
                  "JOIN companies c ON c.id = p.company_id WHERE p.peer_group_name = ? "
                  "ORDER BY p.is_benchmark DESC, p.company_id", (group_name,))


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name):
    return _query("SELECT * FROM peer_percentiles WHERE peer_group_name = ?", (group_name,))


@st.cache_data(ttl=600)
def get_valuation(ticker=None):
    from src.analytics.valuation import build_valuation
    df = build_valuation(DB_PATH)
    return df if ticker is None else df[df["company_id"] == ticker].reset_index(drop=True)


@st.cache_data(ttl=600)
def get_universe(year):
    # one row per company for a financial year: ratios + P&L sales/profit + market data + sector
    year = int(year)
    fr = _annual(_query("SELECT * FROM financial_ratios"), "net_profit_margin_pct")
    fr = fr[fr["fy"] == year]
    pl = _annual(_query("SELECT company_id, year, sales AS sales_cr, net_profit AS net_profit_cr "
                        "FROM profitandloss"), "sales_cr")
    pl = pl[pl["fy"] == year][["company_id", "sales_cr", "net_profit_cr"]]
    mc = _query("SELECT company_id, market_cap_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct "
                "FROM market_cap WHERE year = ?", (year,))
    df = fr.merge(pl, on="company_id", how="left").merge(mc, on="company_id", how="left")
    return df.merge(get_companies()[["company_id", "company_name", "broad_sector", "sub_sector"]],
                    on="company_id", how="left")


@st.cache_data(ttl=600)
def get_screener_universe():
    from src.screener import engine as E
    return E.get_universe(DB_PATH)


@st.cache_data(ttl=600)
def get_screener_config():
    from src.screener import engine as E
    return E.load_config(os.path.join(ROOT, "config", "screener_config.yaml"))


@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    return _query("SELECT pros, cons FROM prosandcons WHERE company_id = ?", (ticker,))


@st.cache_data(ttl=600)
def get_reports(ticker):
    df = _query("SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year DESC", (ticker,))
    return df


@st.cache_data(ttl=600)
def get_capital_patterns():
    # latest pattern per company from output/capital_allocation.csv (made by the ratio engine)
    if not os.path.exists(CAPITAL_CSV):
        return pd.DataFrame(columns=["company_id", "year", "pattern_label", "company_name"])
    df = pd.read_csv(CAPITAL_CSV)
    df = df.sort_values(["company_id", "year"]).groupby("company_id").tail(1)
    return df.merge(get_companies()[["company_id", "company_name", "broad_sector"]], on="company_id", how="left")
