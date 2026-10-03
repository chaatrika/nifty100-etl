# Unit tests for the KPI formulas - Sprint 2
# Run with:  python3 -m pytest tests/kpi -q

import pytest

from src.analytics import cagr as C
from src.analytics import cashflow_kpis as K
from src.analytics import ratios as R

# ---------- Day 08 : profit ratios ----------


def test_net_profit_margin_normal():
    assert R.net_profit_margin(20, 200) == pytest.approx(10)


def test_net_profit_margin_zero_sales():
    assert R.net_profit_margin(20, 0) is None


def test_roe_normal():
    assert R.return_on_equity(30, 50, 100) == pytest.approx(20)


def test_roe_negative_equity():
    assert R.return_on_equity(30, 50, -80) is None


def test_roce_normal():
    assert R.return_on_capital_employed(40, 50, 100, 50) == pytest.approx(20)


def test_roa_zero_assets():
    assert R.return_on_assets(10, 0) is None


def test_opm_mismatch_is_flagged():
    assert R.opm_mismatch(20.0, 15.0) is True


def test_opm_close_values_are_fine():
    assert R.opm_mismatch(20.0, 20.5) is False


# ---------- Day 09 : debt and efficiency ----------


def test_de_no_borrowings_is_zero():
    assert R.debt_to_equity(0, 50, 100) == 0


def test_de_normal():
    assert R.debt_to_equity(150, 50, 100) == pytest.approx(1)


def test_icr_zero_interest_is_none():
    assert R.interest_coverage(100, 10, 0) is None


def test_icr_label_debt_free():
    assert R.icr_label(None, 0) == "Debt Free"


def test_icr_normal():
    assert R.interest_coverage(90, 10, 20) == pytest.approx(5)


def test_icr_warning_below_1_5():
    assert R.icr_warning_flag(1.2) is True


def test_high_leverage_flag_and_bank_exception():
    assert R.high_leverage_flag(6, "Industrials") is True
    assert R.high_leverage_flag(12, "Financials") is False


def test_net_debt_and_asset_turnover():
    assert R.net_debt(100, 30) == 70
    assert R.asset_turnover(200, 100) == pytest.approx(2)


# ---------- Day 10 : CAGR ----------


def test_cagr_normal():
    value, flag = C.cagr(100, 200, 5)
    assert flag == "OK"
    assert value == pytest.approx(14.87, abs=0.01)


def test_cagr_decline_to_loss():
    assert C.cagr(100, -20, 3) == (None, "DECLINE_TO_LOSS")


def test_cagr_turnaround():
    assert C.cagr(-50, 20, 3) == (None, "TURNAROUND")


def test_cagr_both_negative():
    assert C.cagr(-50, -20, 3) == (None, "BOTH_NEGATIVE")


def test_cagr_zero_base():
    assert C.cagr(0, 20, 3) == (None, "ZERO_BASE")


def test_cagr_not_enough_years():
    assert C.cagr_from_series({2023: 100, 2024: 120}, 5) == (None, "INSUFFICIENT")


def test_cagr_from_series_normal():
    value, flag = C.cagr_from_series({2019: 100, 2024: 200}, 5)
    assert flag == "OK"
    assert value == pytest.approx(14.87, abs=0.01)


def test_all_cagrs_has_flags():
    out = C.all_cagrs({2022: 100, 2025: 133.1}, "revenue")
    assert out["revenue_cagr_3yr"] == pytest.approx(10, rel=1e-3)
    assert out["revenue_cagr_5yr_flag"] == "INSUFFICIENT"


def test_cagr_missing_start_value():
    assert C.cagr(None, 10, 3) == (None, "INSUFFICIENT")


def test_cagr_end_zero_gives_minus_100():
    value, flag = C.cagr(100, 0, 3)
    assert value == pytest.approx(-100)


# ---------- Day 11 : cash flow ----------


def test_fcf_can_be_negative():
    assert K.free_cash_flow(50, -80) == -30


def test_cfo_quality_labels():
    assert K.cfo_quality_label(1.2) == "High Quality"
    assert K.cfo_quality_label(0.7) == "Moderate"
    assert K.cfo_quality_label(0.2) == "Accrual Risk"


def test_cfo_quality_profit_zero():
    assert K.cfo_quality_score([10], [0]) is None


def test_capex_labels():
    assert K.capex_label(K.capex_intensity(-20, 1000)) == "Asset Light"
    assert K.capex_label(K.capex_intensity(-50, 1000)) == "Moderate"
    assert K.capex_label(K.capex_intensity(-150, 1000)) == "Capital Intensive"


def test_fcf_conversion_zero_operating_profit():
    assert K.fcf_conversion(10, 0) is None


def test_capital_allocation_patterns():
    assert K.classify_pattern(10, -5, -5, 0.8) == "Reinvestor"
    assert K.classify_pattern(10, -5, -5, 1.4) == "Shareholder Returns"
    assert K.classify_pattern(-10, 5, 5) == "Distress Signal"
    assert K.classify_pattern(10, 5, 5) == "Cash Accumulator"
    assert K.classify_pattern(-10, -5, 5) == "Growth Funded by Debt"
