# db.py - shared database helpers for the API (Sprint 6, Day 38)
import os
import sqlite3
import time

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(ROOT, "output")
REPORTS_DIR = os.path.join(ROOT, "reports")

START_TIME = time.time()
VERSION = "1.0.0"

ALL_TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "market_cap",
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_df(sql, params=()):
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def table_row_counts():
    conn = get_connection()
    try:
        counts = {}
        for table in ALL_TABLES:
            counts[table] = conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
        return counts
    finally:
        conn.close()


def uptime_seconds():
    return round(time.time() - START_TIME, 1)


def latest_ratios():
    # one row per company: the latest year with real profit data
    df = query_df("SELECT * FROM financial_ratios")
    df = df[df["net_profit_margin_pct"].notna()].copy()
    df["fy"] = df["year"].str[:4].astype(int)
    df = df.sort_values(["company_id", "year"]).drop_duplicates(
        ["company_id", "fy"], keep="last"
    )
    return df.sort_values(["company_id", "fy"]).groupby("company_id").tail(1)


def company_or_404(ticker):
    from fastapi import HTTPException

    ticker = ticker.upper()
    row = query_df("SELECT * FROM companies WHERE id = ?", (ticker,))
    if len(row) == 0:
        raise HTTPException(status_code=404, detail="Company '%s' not found" % ticker)
    return ticker


def clean_records(df):
    """Turn a DataFrame into a list of dicts with NaN/NaT replaced by None (valid JSON)."""
    import numpy as np

    return df.replace({np.nan: None}).to_dict("records")
