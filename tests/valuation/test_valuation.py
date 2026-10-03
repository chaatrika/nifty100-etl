import pandas as pd

from src.analytics import valuation as V


def test_flag_rules():
    assert V.flag_for(31, 20) == "Caution"     # above 20 x 1.5
    assert V.flag_for(30, 20) == "Fair"        # exactly 1.5x is not above it
    assert V.flag_for(13, 20) == "Discount"    # below 20 x 0.7
    assert V.flag_for(14, 20) == "Fair"
    assert V.flag_for(None, 20) == "N/A"
    assert V.flag_for(20, float("nan")) == "N/A"


def test_summary_shape_and_columns():
    df = V.build_valuation()
    assert len(df) == 92
    assert list(df.columns) == V.COLUMNS
    assert set(df["flag"]) <= {"Caution", "Discount", "Fair", "N/A"}
    assert df["company_id"].is_unique


def test_fcf_yield_formula():
    df = V.build_valuation()
    row = df.dropna(subset=["FCF_yield_pct"]).iloc[0]
    assert pd.notna(row["FCF_yield_pct"])
