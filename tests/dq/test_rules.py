# Unit tests for the data quality rules DQ-01 to DQ-16 (validator.py)
# Sprint 3, Day 21. Each rule has one test with a bad row (must be flagged)
# and a good row (must not be flagged).

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "etl"))
import validator as V


def test_dq01_duplicate_company_id():
    bad = pd.DataFrame({"id": ["TCS", "TCS", "INFY"]})
    good = pd.DataFrame({"id": ["TCS", "INFY"]})
    assert len(V.dq01_company_pk_uniqueness(bad)) == 2
    assert V.dq01_company_pk_uniqueness(good) == []


def test_dq02_duplicate_company_year():
    bad = pd.DataFrame({"company_id": ["TCS", "TCS"], "year": ["2023-03", "2023-03"]})
    good = pd.DataFrame({"company_id": ["TCS", "TCS"], "year": ["2023-03", "2024-03"]})
    assert len(V.dq02_annual_pk_uniqueness(bad, "profitandloss")) == 2
    assert V.dq02_annual_pk_uniqueness(good, "profitandloss") == []


def test_dq03_orphan_company():
    df = pd.DataFrame({"company_id": ["TCS", "XYZ"], "year": ["2023-03", "2023-03"]})
    result = V.dq03_fk_integrity(df, {"TCS"}, "profitandloss")
    assert len(result) == 1
    assert result[0]["company_id"] == "XYZ"
    assert result[0]["severity"] == "CRITICAL"


def test_dq04_balance_sheet_mismatch():
    bs = pd.DataFrame(
        {
            "company_id": ["A", "B"],
            "year": ["2023-03", "2023-03"],
            "total_assets": [1000, 1000],
            "total_liabilities": [1000, 900],
        }
    )
    result = V.dq04_balance_sheet_balance(bs)
    assert len(result) == 1
    assert result[0]["company_id"] == "B"


def test_dq05_opm_mismatch():
    pl = pd.DataFrame(
        {
            "company_id": ["A", "B"],
            "year": ["2023-03", "2023-03"],
            "sales": [100, 100],
            "operating_profit": [20, 20],
            "opm_percentage": [20, 35],
        }
    )
    result = V.dq05_opm_cross_check(pl)
    assert len(result) == 1
    assert result[0]["company_id"] == "B"


def test_dq06_non_positive_sales_and_banks_skipped():
    pl = pd.DataFrame(
        {"company_id": ["A", "BANK"], "year": ["2023-03", "2023-03"], "sales": [-5, -5]}
    )
    result = V.dq06_positive_sales(pl, {"BANK"})
    assert len(result) == 1
    assert result[0]["company_id"] == "A"


def test_dq07_bad_year_format():
    df = pd.DataFrame({"company_id": ["A", "A"], "year": ["2023-03", "March 2023"]})
    result = V.dq07_year_format(df, "profitandloss")
    assert len(result) == 1
    assert result[0]["severity"] == "CRITICAL"


def test_dq08_ticker_length():
    df = pd.DataFrame({"id": ["TCS", "X", "ABCDEFGHIJKLM"]})
    assert len(V.dq08_ticker_format(df)) == 2


def test_dq09_net_cash_mismatch():
    cf = pd.DataFrame(
        {
            "company_id": ["A", "B"],
            "year": ["2023-03", "2023-03"],
            "operating_activity": [100, 100],
            "investing_activity": [-50, -50],
            "financing_activity": [-20, -20],
            "net_cash_flow": [30, 80],
        }
    )
    result = V.dq09_net_cash_check(cf)
    assert len(result) == 1
    assert result[0]["company_id"] == "B"


def test_dq10_negative_fixed_assets():
    bs = pd.DataFrame(
        {
            "company_id": ["A", "B"],
            "year": ["2023-03", "2023-03"],
            "fixed_assets": [100, -5],
        }
    )
    result = V.dq10_non_negative_fixed_assets(bs)
    assert len(result) == 1
    assert result[0]["company_id"] == "B"


def test_dq11_tax_rate_out_of_range():
    pl = pd.DataFrame(
        {
            "company_id": ["A", "B", "C"],
            "year": ["2023-03"] * 3,
            "tax_percentage": [25, 75, -3],
        }
    )
    assert len(V.dq11_tax_rate_range(pl)) == 2


def test_dq12_dividend_payout_over_200():
    pl = pd.DataFrame(
        {
            "company_id": ["A", "B"],
            "year": ["2023-03"] * 2,
            "dividend_payout": [40, 250],
        }
    )
    result = V.dq12_dividend_payout_cap(pl)
    assert len(result) == 1
    assert result[0]["company_id"] == "B"


def test_dq13_missing_report_url():
    docs = pd.DataFrame(
        {
            "company_id": ["A", "B", "C"],
            "year": [2023, 2023, 2023],
            "annual_report": ["http://x.com/a.pdf", "", None],
        }
    )
    assert len(V.dq13_url_validity_documents(docs)) == 2


def test_dq14_eps_sign_mismatch():
    pl = pd.DataFrame(
        {
            "company_id": ["A", "B"],
            "year": ["2023-03"] * 2,
            "net_profit": [100, 100],
            "eps": [5, -2],
        }
    )
    result = V.dq14_eps_sign_consistency(pl)
    assert len(result) == 1
    assert result[0]["company_id"] == "B"


def test_dq15_strict_balance_is_info_only():
    bs = pd.DataFrame(
        {
            "company_id": ["A"],
            "year": ["2023-03"],
            "total_assets": [1000],
            "total_liabilities": [999],
        }
    )
    result = V.dq15_bse_ase_balance_strict(bs)
    assert len(result) == 1
    assert result[0]["severity"] == "INFO"


def test_dq16_short_history_flagged():
    years = ["2019-03", "2020-03", "2021-03", "2022-03", "2023-03"]
    pl = pd.DataFrame(
        {"company_id": ["LONG"] * 5 + ["SHORT"] * 2, "year": years + years[:2]}
    )
    empty = pd.DataFrame({"company_id": [], "year": []})
    result = V.dq16_coverage_check(pl, empty, empty, {"LONG", "SHORT"})
    assert len(result) == 1
    assert result[0]["company_id"] == "SHORT"
