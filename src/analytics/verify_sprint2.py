# verify_sprint2.py
# Quick checks for Day 12 and Day 14.
# Run:  python3 -m src.analytics.verify_sprint2 [COMPANY_ID ...]

import sqlite3
import sys

import pandas as pd

DB_PATH = "data/nifty100.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)

    # 1. row count
    print("1. rows:", len(fr), "(need 1100 or more)", "PASS" if len(fr) >= 1100 else "FAIL")

    # 2. columns that are completely empty
    kpi_cols = [c for c in fr.columns if c not in ("row_id", "company_id", "year")]
    empty = [c for c in kpi_cols if fr[c].isna().all()]
    if len(empty) == 0:
        print("2. empty columns: none PASS")
    else:
        print("2. empty columns:", empty, "FAIL")

    # latest year that has profit data (some companies have a later balance-sheet-only row)
    with_data = fr[fr["net_profit_margin_pct"].notna()]
    latest = with_data.sort_values("year").groupby("company_id").tail(1)

    # 3. screener: ROE > 15 and D/E < 1
    screen = latest[(latest["return_on_equity_pct"] > 15) & (latest["debt_to_equity"] < 1)]
    ok = 15 <= len(screen) <= 50
    print("3. screener ROE>15 and D/E<1:", len(screen), "companies (expected 15 to 50)", "PASS" if ok else "CHECK")
    print("   ", ", ".join(sorted(screen["company_id"])))

    # 4. numbers to recompute by hand in a spreadsheet
    ids = sys.argv[1:]
    if len(ids) == 0:
        ids = ["TCS", "HDFCBANK", "RELIANCE"]
    print("4. spot check - recompute ROE and 5yr revenue CAGR by hand:")
    for cid in ids:
        rows = latest[latest["company_id"] == cid]
        if len(rows) == 0:
            print("   ", cid, "not found")
            continue
        r = rows.iloc[0]
        pl = pd.read_sql("SELECT sales, net_profit FROM profitandloss WHERE company_id=? AND year=?",
                         conn, params=(cid, r["year"]))
        bs = pd.read_sql("SELECT equity_capital, reserves FROM balancesheet WHERE company_id=? AND year=?",
                         conn, params=(cid, r["year"]))
        print("   %s %s: ROE=%.2f  revenue CAGR 5yr=%s (%s)" % (
            cid, r["year"], r["return_on_equity_pct"], r["revenue_cagr_5yr"], r["revenue_cagr_5yr_flag"]))
        print("      P&L:", pl.to_dict("records"), " BS:", bs.to_dict("records"))


if __name__ == "__main__":
    main()
