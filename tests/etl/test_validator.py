import pytest
import pandas as pd
from src.etl.validator import validate_null_values, validate_financial_integrity

def test_validate_null_values():
    data = pd.DataFrame([
        {"company_id": 1, "ticker": "TCS"},
        {"company_id": 2, "ticker": None}
    ])
    failures = validate_null_values(data, ["ticker"], "companies")
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-02"

def test_validate_financial_integrity_negative():
    data = pd.DataFrame([
        {"company_id": 1, "year": 2021, "sales": -500.0}
    ])
    failures = validate_financial_integrity(data, "profitandloss")
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-03"

def test_validate_financial_integrity_imbalance():
    data = pd.DataFrame([
        {"company_id": 1, "year": 2021, "total_assets": 1000.0, "total_liabilities": 800.0}
    ])
    failures = validate_financial_integrity(data, "balancesheet")
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-04"
