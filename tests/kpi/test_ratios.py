# 20 unit tests for the ratio formulas (Sprint 6, Day 41)
import pytest

from src.analytics import cagr as C
from src.analytics import cashflow_kpis as K
from src.analytics import ratios as R


def test_roe_positive_equity():
    assert R.return_on_equity(30, 50, 100) == pytest.approx(20)


def test_roe_negative_equity_returns_none():
    assert R.return_on_equity(30, 50, -80) is None


def test_de_debt_free_returns_zero():
    assert R.debt_to_equity(0, 50, 100) == 0


def test_icr_interest_zero_returns_none():
    assert R.interest_coverage(100, 10, 0) is None


def test_de_over_5_flag_non_financial():
    assert R.high_leverage_flag(6, "Industrials") is True


def test_de_over_5_flag_skipped_for_financials():
    assert R.high_leverage_flag(6, "Financials") is False


def test_cagr_turnaround_flag():
    assert C.cagr(-50, 20, 3) == (None, "TURNAROUND")


def test_cagr_decline_to_loss_flag():
    assert C.cagr(100, -20, 3) == (None, "DECLINE_TO_LOSS")


def test_cagr_normal_calculation():
    value, flag = C.cagr(100, 200, 5)
    assert flag == "OK"
    assert value == pytest.approx(14.87, abs=0.01)


def test_opm_cross_check_divergence_flag():
    assert R.opm_mismatch(20.0, 15.0) is True


def test_cfo_quality_score_calculation():
    score = K.cfo_quality_score([120, 110, 100, 90, 80], [100, 100, 100, 100, 100])
    assert score == pytest.approx(1.0)


def test_roa_zero_assets_returns_none():
    assert R.return_on_assets(10, 0) is None


def test_net_profit_margin_normal():
    assert R.net_profit_margin(20, 200) == pytest.approx(10)


def test_asset_turnover_normal():
    assert R.asset_turnover(200, 100) == pytest.approx(2)


def test_icr_debt_free_label():
    assert R.icr_label(None, 0) == "Debt Free"


def test_icr_warning_below_threshold():
    assert R.icr_warning_flag(1.2) is True


def test_net_debt_calculation():
    assert R.net_debt(100, 30) == 70


def test_cagr_both_negative_flag():
    assert C.cagr(-50, -20, 3) == (None, "BOTH_NEGATIVE")


def test_cagr_zero_base_flag():
    assert C.cagr(0, 20, 3) == (None, "ZERO_BASE")


def test_roce_normal_calculation():
    assert R.return_on_capital_employed(40, 50, 100, 50) == pytest.approx(20)
