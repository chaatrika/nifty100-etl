"""Excel -> SQLite loader for the Nifty 100 Financial Intelligence Platform.

Sprint 1 (Days 01-07). Loads all 7 core + 5 supplementary Excel files,
normalises tickers/years, deduplicates, validates FK integrity, writes the
10-table SQLite database, and produces load_audit.csv + validation_failures.csv.

Run: python src/etl/loader.py   (or: make load)
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from normaliser import normalize_year, normalize_ticker  # noqa: E402
import validator  # noqa: E402

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
SUPP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "supporting")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "nifty100.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema.sql")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")

CORE_FILES = ["companies", "profitandloss", "balancesheet", "cashflow",
              "analysis", "documents", "prosandcons"]
SUPP_FILES = ["sectors", "stock_prices", "market_cap", "financial_ratios", "peer_groups"]

TIME_SERIES_TABLES = ["profitandloss", "balancesheet", "cashflow"]


def load_core_excel() -> dict:
    """Load all 7 core files with header=1 (row 0 is metadata)."""
    tables = {}
    for name in CORE_FILES:
        path = os.path.join(RAW_DIR, f"{name}.xlsx")
        df = pd.read_excel(path, header=1)
        tables[name] = df
    return tables


def load_supplementary_excel() -> dict:
    """Load all 5 supplementary files with header=0."""
    tables = {}
    for name in SUPP_FILES:
        path = os.path.join(SUPP_DIR, f"{name}.xlsx")
        df = pd.read_excel(path, header=0)
        tables[name] = df
    return tables


def normalise_tables(tables: dict) -> dict:
    """Apply ticker/year normalisation to every table that has company_id / year columns."""
    for name, df in tables.items():
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].apply(normalize_ticker)
        if "id" in df.columns and name == "companies":
            df["id"] = df["id"].apply(normalize_ticker)
        if "company_name" in df.columns:
            df["company_name"] = df["company_name"].astype(str).str.replace("\n", " ", regex=False).str.strip()
        if "year" in df.columns and name in TIME_SERIES_TABLES + ["financial_ratios"]:
            df["year"] = df["year"].apply(normalize_year)
        tables[name] = df
    return tables


def dedup_tables(tables: dict, audit_rows: list) -> dict:
    """Deduplicate (company_id, year) pairs in time-series tables: keep last occurrence."""
    for name in TIME_SERIES_TABLES + ["financial_ratios", "market_cap"]:
        df = tables[name]
        before = len(df)
        df = df.drop_duplicates(subset=["company_id", "year"], keep="last")
        after = len(df)
        if before != after:
            for row in audit_rows:
                if row["table"] == name:
                    row["duplicates_removed"] = before - after
        tables[name] = df
    # stock_prices dedups on (company_id, date)
    df = tables["stock_prices"]
    before = len(df)
    df = df.drop_duplicates(subset=["company_id", "date"], keep="last")
    tables["stock_prices"] = df
    return tables


def reject_orphans_and_bad_rows(tables: dict, audit_rows: list) -> dict:
    """Reject rows failing critical checks: null company_id / unparseable year / orphan FK."""
    valid_ids = set(tables["companies"]["id"].dropna())
    for name, df in tables.items():
        if name == "companies":
            before = len(df)
            df = df[df["id"].notna()]
            rejected = before - len(df)
        elif "company_id" in df.columns:
            before = len(df)
            df = df[df["company_id"].notna() & df["company_id"].isin(valid_ids)]
            if "year" in df.columns and name in TIME_SERIES_TABLES + ["financial_ratios"]:
                df = df[df["year"].notna()]
            rejected = before - len(df)
        else:
            rejected = 0
        tables[name] = df
        for row in audit_rows:
            if row["table"] == name:
                row["rejected"] += rejected
    return tables


def rename_for_schema(tables: dict) -> dict:
    """Rename source columns to match the SQLite schema (row_id, annual_report, etc.)."""
    if "id" in tables["profitandloss"].columns:
        tables["profitandloss"] = tables["profitandloss"].rename(columns={"id": "row_id"})
    if "id" in tables["balancesheet"].columns:
        tables["balancesheet"] = tables["balancesheet"].rename(columns={"id": "row_id"})
    if "id" in tables["cashflow"].columns:
        cf = tables["cashflow"].rename(columns={"id": "row_id"})
        if "net_cash_flow" not in cf.columns:
            cf["net_cash_flow"] = cf["operating_activity"].fillna(0) + \
                                   cf["investing_activity"].fillna(0) + \
                                   cf["financing_activity"].fillna(0)
        tables["cashflow"] = cf
    if "id" in tables["analysis"].columns:
        tables["analysis"] = tables["analysis"].rename(columns={"id": "row_id"})
    if "id" in tables["documents"].columns:
        tables["documents"] = tables["documents"].rename(
            columns={"id": "row_id", "Year": "year", "Annual_Report": "annual_report"})
        tables["documents"] = tables["documents"].rename(columns={"year": "year"})
        # normalise capital 'Year' -> 'year' already done above; ensure final name matches schema
    if "id" in tables["prosandcons"].columns:
        tables["prosandcons"] = tables["prosandcons"].rename(columns={"id": "row_id"})
    if "id" in tables["sectors"].columns:
        tables["sectors"] = tables["sectors"].rename(columns={"id": "row_id"})
    if "id" in tables["stock_prices"].columns:
        tables["stock_prices"] = tables["stock_prices"].rename(columns={"id": "row_id"})
    if "id" in tables["market_cap"].columns:
        tables["market_cap"] = tables["market_cap"].rename(columns={"id": "row_id"})
    if "id" in tables["financial_ratios"].columns:
        tables["financial_ratios"] = tables["financial_ratios"].rename(columns={"id": "row_id"})
    if "id" in tables["peer_groups"].columns:
        tables["peer_groups"] = tables["peer_groups"].rename(columns={"id": "row_id"})
    # documents.year -> ensure integer
    if "year" in tables["documents"].columns:
        tables["documents"]["year"] = pd.to_numeric(tables["documents"]["year"], errors="coerce").astype("Int64")
    return tables


def write_to_sqlite(tables: dict):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    schema_cols = {
        "companies": ["id", "company_logo", "company_name", "chart_link", "about_company", "website",
                      "nse_profile", "bse_profile", "face_value", "book_value", "roce_percentage", "roe_percentage"],
        "profitandloss": ["row_id", "company_id", "year", "sales", "expenses", "operating_profit",
                           "opm_percentage", "other_income", "interest", "depreciation", "profit_before_tax",
                           "tax_percentage", "net_profit", "eps", "dividend_payout"],
        "balancesheet": ["row_id", "company_id", "year", "equity_capital", "reserves", "borrowings",
                          "other_liabilities", "total_liabilities", "fixed_assets", "cwip", "investments",
                          "other_asset", "total_assets"],
        "cashflow": ["row_id", "company_id", "year", "operating_activity", "investing_activity",
                     "financing_activity", "net_cash_flow"],
        "analysis": ["row_id", "company_id", "compounded_sales_growth", "compounded_profit_growth",
                     "stock_price_cagr", "roe"],
        "documents": ["row_id", "company_id", "year", "annual_report"],
        "prosandcons": ["row_id", "company_id", "pros", "cons"],
        "sectors": ["row_id", "company_id", "broad_sector", "sub_sector", "index_weight_pct", "market_cap_category"],
        "stock_prices": ["row_id", "company_id", "date", "open_price", "high_price", "low_price",
                          "close_price", "volume", "adjusted_close"],
        "market_cap": ["row_id", "company_id", "year", "market_cap_crore", "enterprise_value_crore",
                        "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"],
        "financial_ratios": ["row_id", "company_id", "year", "net_profit_margin_pct", "operating_profit_margin_pct",
                              "return_on_equity_pct", "debt_to_equity", "interest_coverage", "asset_turnover",
                              "free_cash_flow_cr", "capex_cr", "earnings_per_share", "book_value_per_share",
                              "dividend_payout_ratio_pct", "total_debt_cr", "cash_from_operations_cr"],
        "peer_groups": ["row_id", "peer_group_name", "company_id", "is_benchmark"],
    }

    for table, cols in schema_cols.items():
        df = tables[table]
        cols_present = [c for c in cols if c in df.columns]
        df[cols_present].to_sql(table, conn, if_exists="append", index=False)

    conn.commit()
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()
    return fk_violations


def main():
    start = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading core Excel files (header=1)...")
    core = load_core_excel()
    print("Loading supplementary Excel files (header=0)...")
    supp = load_supplementary_excel()
    tables = {**core, **supp}

    audit_rows = [{"table": name, "rows_in": len(df), "rejected": 0, "duplicates_removed": 0}
                  for name, df in tables.items()]

    print("Normalising tickers and years...")
    tables = normalise_tables(tables)

    # Run DQ rules BEFORE dedup/rejection so every violation (including rows
    # that are about to be dropped, e.g. orphan FKs / unparseable years) is
    # captured in validation_failures.csv.
    print("Running 16 DQ validation rules...")
    bank_ids = set()
    if "sectors" in tables:
        bank_rows = tables["sectors"]
        bank_ids = set(bank_rows.loc[bank_rows["broad_sector"] == "Financials", "company_id"].dropna())
    violations_df = validator.run_all_rules(tables, bank_ids)
    violations_df.to_csv(os.path.join(OUTPUT_DIR, "validation_failures.csv"), index=False)

    critical = violations_df[violations_df["severity"] == "CRITICAL"]
    print(f"DQ rules complete: {len(violations_df)} total findings, {len(critical)} CRITICAL "
          f"(all CRITICAL rows are excluded from the load below).")

    print("Deduplicating time-series tables...")
    tables = dedup_tables(tables, audit_rows)

    print("Rejecting orphan/invalid rows...")
    tables = reject_orphans_and_bad_rows(tables, audit_rows)

    print("Renaming columns to match schema...")
    tables = rename_for_schema(tables)

    print("Writing to SQLite (nifty100.db)...")
    fk_violations = write_to_sqlite(tables)

    runtime = time.time() - start
    for row in audit_rows:
        name = row["table"]
        row["rows_out"] = len(tables[name])
        row["timestamp"] = pd.Timestamp.now().isoformat()
        row["runtime_s"] = round(runtime, 2)

    audit_df = pd.DataFrame(audit_rows, columns=["table", "rows_in", "rows_out", "rejected",
                                                  "duplicates_removed", "timestamp", "runtime_s"])
    audit_df.to_csv(os.path.join(OUTPUT_DIR, "load_audit.csv"), index=False)

    print(f"\nLoad complete in {runtime:.2f}s.")
    print(f"FK check violations: {len(fk_violations)}")
    print(audit_df[["table", "rows_in", "rows_out", "rejected", "duplicates_removed"]].to_string(index=False))

    if fk_violations:
        print("WARNING: FK violations found:", fk_violations[:5])

    return audit_df, violations_df, fk_violations


if __name__ == "__main__":
    main()
