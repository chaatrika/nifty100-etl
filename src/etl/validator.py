"""Data Quality validator — 16 rules (DQ-01 .. DQ-16). Sprint 1, Day 03.

Each check function returns a list of violation dicts:
    {company_id, year, field, issue, severity}
severity is one of CRITICAL / WARNING / INFO.
"""

from __future__ import annotations

import pandas as pd
from typing import List, Dict


def _violation(company_id, year, field, issue, severity) -> Dict:
    return {
        "company_id": company_id,
        "year": year,
        "field": field,
        "issue": issue,
        "severity": severity,
    }


def dq01_company_pk_uniqueness(companies: pd.DataFrame) -> List[Dict]:
    v = []
    dupes = companies[companies.duplicated(subset=["id"], keep=False)]
    for _, row in dupes.iterrows():
        v.append(_violation(row["id"], None, "id", "Duplicate company id (PK)", "CRITICAL"))
    return v


def dq02_annual_pk_uniqueness(df: pd.DataFrame, table_name: str) -> List[Dict]:
    v = []
    dupes = df[df.duplicated(subset=["company_id", "year"], keep=False)]
    for _, row in dupes.iterrows():
        v.append(_violation(row["company_id"], row["year"], f"{table_name}.(company_id,year)",
                             "Duplicate (company_id, year) pair", "CRITICAL"))
    return v


def dq03_fk_integrity(df: pd.DataFrame, valid_ids: set, table_name: str) -> List[Dict]:
    v = []
    orphans = df[~df["company_id"].isin(valid_ids)]
    for _, row in orphans.iterrows():
        v.append(_violation(row["company_id"], row.get("year"), f"{table_name}.company_id",
                             "Orphan row — company_id not in companies.id", "CRITICAL"))
    return v


def dq04_balance_sheet_balance(bs: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in bs.iterrows():
        ta, tl = row.get("total_assets"), row.get("total_liabilities")
        if pd.isna(ta) or pd.isna(tl) or ta == 0:
            continue
        if abs(ta - tl) / abs(ta) >= 0.01:
            v.append(_violation(row["company_id"], row["year"], "total_assets/total_liabilities",
                                 f"Balance mismatch: assets={ta}, liabilities={tl}", "WARNING"))
    return v


def dq05_opm_cross_check(pl: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in pl.iterrows():
        sales, op, opm = row.get("sales"), row.get("operating_profit"), row.get("opm_percentage")
        if pd.isna(sales) or sales == 0 or pd.isna(op) or pd.isna(opm):
            continue
        computed = op / sales * 100
        if abs(opm - computed) >= 1.0:
            v.append(_violation(row["company_id"], row["year"], "opm_percentage",
                                 f"OPM mismatch: reported={opm}, computed={computed:.2f}", "WARNING"))
    return v


def dq06_positive_sales(pl: pd.DataFrame, bank_ids: set) -> List[Dict]:
    v = []
    for _, row in pl.iterrows():
        if row["company_id"] in bank_ids:
            continue
        sales = row.get("sales")
        if pd.notna(sales) and sales <= 0:
            v.append(_violation(row["company_id"], row["year"], "sales",
                                 f"Non-positive sales: {sales}", "WARNING"))
    return v


def dq07_year_format(df: pd.DataFrame, table_name: str) -> List[Dict]:
    import re
    v = []
    pat = re.compile(r"^\d{4}-\d{2}$")
    for _, row in df.iterrows():
        y = row.get("year")
        if y is None or not pat.match(str(y)):
            v.append(_violation(row.get("company_id"), y, f"{table_name}.year",
                                 f"Unparseable year value: {y}", "CRITICAL"))
    return v


def dq08_ticker_format(companies: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in companies.iterrows():
        cid = row["id"]
        if cid is None or not (2 <= len(str(cid)) <= 12):
            v.append(_violation(cid, None, "id", "Ticker length out of range (2-12)", "CRITICAL"))
    return v


def dq09_net_cash_check(cf: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in cf.iterrows():
        cfo, cfi, cff, net = (row.get("operating_activity"), row.get("investing_activity"),
                               row.get("financing_activity"), row.get("net_cash_flow"))
        if any(pd.isna(x) for x in (cfo, cfi, cff, net)):
            continue
        if abs(net - (cfo + cfi + cff)) > 10:
            v.append(_violation(row["company_id"], row["year"], "net_cash_flow",
                                 f"net_cash_flow mismatch vs CFO+CFI+CFF (tol 10 Cr)", "WARNING"))
    return v


def dq10_non_negative_fixed_assets(bs: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in bs.iterrows():
        fa = row.get("fixed_assets")
        if pd.notna(fa) and fa < 0:
            v.append(_violation(row["company_id"], row["year"], "fixed_assets",
                                 f"Negative fixed_assets: {fa} (coerced to 0)", "WARNING"))
    return v


def dq11_tax_rate_range(pl: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in pl.iterrows():
        t = row.get("tax_percentage")
        if pd.notna(t) and not (0 <= t <= 60):
            v.append(_violation(row["company_id"], row["year"], "tax_percentage",
                                 f"Tax rate out of range: {t}", "WARNING"))
    return v


def dq12_dividend_payout_cap(pl: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in pl.iterrows():
        d = row.get("dividend_payout")
        if pd.notna(d) and d > 200:
            v.append(_violation(row["company_id"], row["year"], "dividend_payout",
                                 f"Dividend payout >200%: {d}", "WARNING"))
    return v


def dq13_url_validity_documents(docs: pd.DataFrame) -> List[Dict]:
    # Network validation (requests.head) is skipped offline; flag only null/empty URLs.
    v = []
    for _, row in docs.iterrows():
        url = row.get("annual_report")
        if pd.isna(url) or str(url).strip() == "":
            v.append(_violation(row["company_id"], row.get("year"), "annual_report",
                                 "Missing/empty Annual_Report URL", "WARNING"))
    return v


def dq14_eps_sign_consistency(pl: pd.DataFrame) -> List[Dict]:
    v = []
    for _, row in pl.iterrows():
        eps, np_ = row.get("eps"), row.get("net_profit")
        if pd.isna(eps) or pd.isna(np_):
            continue
        if np_ > 0 and eps <= 0:
            v.append(_violation(row["company_id"], row["year"], "eps",
                                 f"EPS sign mismatch: net_profit={np_}, eps={eps}", "WARNING"))
    return v


def dq15_bse_ase_balance_strict(bs: pd.DataFrame) -> List[Dict]:
    v = []
    count = 0
    for _, row in bs.iterrows():
        ta, tl = row.get("total_assets"), row.get("total_liabilities")
        if pd.notna(ta) and pd.notna(tl) and ta != tl:
            count += 1
    if count:
        v.append(_violation(None, None, "total_assets/total_liabilities",
                             f"{count} rows not strictly balanced (informational)", "INFO"))
    return v


def dq16_coverage_check(pl: pd.DataFrame, bs: pd.DataFrame, cf: pd.DataFrame, all_ids: set) -> List[Dict]:
    v = []
    for cid in all_ids:
        years = set()
        for df in (pl, bs, cf):
            years |= set(df.loc[df["company_id"] == cid, "year"].dropna().unique())
        if len(years) < 5:
            v.append(_violation(cid, None, "coverage",
                                 f"Only {len(years)} distinct years of P&L/BS/CF history (<5)", "WARNING"))
    return v


def run_all_rules(tables: Dict[str, pd.DataFrame], bank_ids: set) -> pd.DataFrame:
    """Run all 16 DQ rules against the loaded (pre-DB) DataFrames and return a violations DataFrame."""
    companies = tables["companies"]
    pl = tables["profitandloss"]
    bs = tables["balancesheet"]
    cf = tables["cashflow"]
    docs = tables["documents"]
    valid_ids = set(companies["id"].dropna())

    violations: List[Dict] = []
    violations += dq01_company_pk_uniqueness(companies)
    for name, df in (("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)):
        violations += dq02_annual_pk_uniqueness(df, name)
    for name, df in (("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf),
                      ("documents", docs), ("analysis", tables["analysis"]),
                      ("prosandcons", tables["prosandcons"])):
        violations += dq03_fk_integrity(df, valid_ids, name)
    violations += dq04_balance_sheet_balance(bs)
    violations += dq05_opm_cross_check(pl)
    violations += dq06_positive_sales(pl, bank_ids)
    for name, df in (("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)):
        violations += dq07_year_format(df, name)
    violations += dq08_ticker_format(companies)
    violations += dq09_net_cash_check(cf)
    violations += dq10_non_negative_fixed_assets(bs)
    violations += dq11_tax_rate_range(pl)
    violations += dq12_dividend_payout_cap(pl)
    violations += dq13_url_validity_documents(docs)
    violations += dq14_eps_sign_consistency(pl)
    violations += dq15_bse_ase_balance_strict(bs)
    violations += dq16_coverage_check(pl, bs, cf, valid_ids)

    return pd.DataFrame(violations, columns=["company_id", "year", "field", "issue", "severity"])
