# Tests for the screener engine (Sprint 3)

import os

import numpy as np
import pandas as pd
import pytest

from src.screener import engine as E

DB_EXISTS = os.path.exists(E.DB_PATH)


def small_universe():
    # 4 made-up companies
    return pd.DataFrame({
        "company_id": ["A", "B", "C", "BANK"],
        "broad_sector": ["IT", "IT", "Energy", "Financials"],
        "return_on_equity_pct": [20, 10, 30, 12],
        "debt_to_equity": [0.5, 0.2, 3.0, 12.0],
        "de_prev": [0.8, 0.1, 4.0, 13.0],
        "free_cash_flow_cr": [100, -5, 50, 10],
        "interest_coverage": [8.0, np.nan, 2.0, 1.2],
        "icr_for_filter": [8.0, np.inf, 2.0, 1.2],
        "composite_quality_score": [70, 60, 50, 40],
    })


def test_roe_min_filter():
    df = small_universe()
    result = E.apply_filters(df, {"roe_min": 15})
    assert list(result["company_id"]) == ["A", "C"]


def test_de_max_skips_financials():
    df = small_universe()
    result = E.apply_filters(df, {"de_max": 1.0})
    # BANK has D/E of 12 but it is a Financials company, so the filter is skipped for it
    assert "BANK" in list(result["company_id"])
    assert "C" not in list(result["company_id"])


def test_debt_free_icr_always_passes():
    df = small_universe()
    result = E.apply_filters(df, {"icr_min": 1000})
    assert list(result["company_id"]) == ["B"]


def test_missing_value_fails_filter():
    df = small_universe()
    df.loc[0, "return_on_equity_pct"] = np.nan
    result = E.apply_filters(df, {"roe_min": 5})
    assert "A" not in list(result["company_id"])


def test_de_declining_filter():
    df = small_universe()
    result = E.apply_filters(df, {"de_declining": True})
    assert set(result["company_id"]) == {"A", "C", "BANK"}


def test_fcf_positive_latest():
    df = small_universe()
    result = E.apply_filters(df, {"fcf_positive_latest": True})
    assert "B" not in list(result["company_id"])


def test_exclude_sectors():
    df = small_universe()
    result = E.apply_filters(df, {"roe_min": 0}, exclude_sectors=["Financials"])
    assert "BANK" not in list(result["company_id"])


def test_result_sorted_by_composite_score():
    df = small_universe()
    result = E.apply_filters(df, {"roe_min": 0})
    scores = list(result["composite_quality_score"])
    assert scores == sorted(scores, reverse=True)


def test_unknown_filter_raises():
    with pytest.raises(ValueError):
        E.apply_filters(small_universe(), {"not_a_filter": 1})


def test_winsor_scale_caps_extremes():
    s = pd.Series(list(range(1, 11)) + [1000])          # one huge outlier
    scaled = E.winsor_scale(s)
    assert scaled.min() == 0
    assert scaled.max() == 100
    assert scaled.iloc[-1] == 100                        # the outlier is capped, not 100x bigger


def test_winsor_scale_lower_is_better():
    s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    scaled = E.winsor_scale(s, lower_is_better=True)
    assert scaled.iloc[0] > scaled.iloc[-1]


def test_config_has_six_presets_and_weights_add_to_100():
    config = E.load_config()
    assert len(config["presets"]) == 6
    assert sum(config["composite_weights"].values()) == 100


@pytest.mark.skipif(not DB_EXISTS, reason="database not found")
def test_each_preset_returns_5_to_50_companies():
    df = E.get_universe()
    config = E.load_config()
    for name, result in E.run_all_presets(df, config).items():
        assert 5 <= len(result) <= 50, name + " returned " + str(len(result))


@pytest.mark.skipif(not DB_EXISTS, reason="database not found")
def test_quality_compounder_meets_roe_and_de_rules():
    df = E.get_universe()
    config = E.load_config()
    result = E.run_preset(df, config, "quality_compounder")
    assert (result["return_on_equity_pct"] >= 15).all()
    non_banks = result[result["broad_sector"] != "Financials"]
    assert (non_banks["debt_to_equity"] <= 1.0).all()


@pytest.mark.skipif(not DB_EXISTS, reason="database not found")
def test_composite_scores_are_between_0_and_100():
    df = E.get_universe()
    assert df["composite_quality_score"].between(0, 100).all()
    assert df["sector_relative_score"].between(0, 100).all()
