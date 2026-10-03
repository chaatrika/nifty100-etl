# series.py - shared loader for the Sprint 5 modules (NLP, cash flow intelligence, PDF reports)
# Financial tables have years like "2024-03". We turn them into a financial year number (fy)
# and keep the LAST row of each fy that has real data (same rule as the dashboard).

import os
import sqlite3

import pandas as pd

DB_PATH = os.path.join("data", "nifty100.db")


def annual(df, key_col):
    df = df[df[key_col].notna()].copy()
    df["fy"] = df["year"].str[:4].astype(int)
    return df.sort_values(["company_id", "year"]).groupby(["company_id", "fy"]).tail(1)


def load_all(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    q = lambda s: pd.read_sql(s, conn)
    data = {
        "companies": q("SELECT c.id AS company_id, c.company_name, c.about_company, s.broad_sector AS sector, "
                       "s.sub_sector FROM companies c LEFT JOIN sectors s ON s.company_id = c.id ORDER BY c.id"),
        "ratios": annual(q("SELECT * FROM financial_ratios"), "net_profit_margin_pct"),
        "pl": annual(q("SELECT * FROM profitandloss"), "sales"),
        "bs": annual(q("SELECT * FROM balancesheet"), "total_assets"),
        "cf": annual(q("SELECT * FROM cashflow"), "operating_activity"),
        "mc": q("SELECT * FROM market_cap"),
    }
    conn.close()
    return data


def by_company(df):
    # {company_id: dataframe sorted by fy}
    return {k: g.sort_values("fy").reset_index(drop=True) for k, g in df.groupby("company_id")}
