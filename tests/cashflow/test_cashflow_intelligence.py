import pandas as pd
import pytest

from src.analytics import capital_report as R
from src.analytics import cashflow_intelligence as CI


@pytest.fixture(scope="module")
def result():
    return CI.build()


def test_92_rows_and_required_columns(result):
    out, _alerts = result
    assert len(out) == 92
    assert list(out.columns) == CI.COLUMNS
    assert out["company_id"].is_unique


def test_labels_are_from_the_allowed_sets(result):
    out, _ = result
    assert set(out["cfo_quality_label"].dropna()) <= {"High Quality", "Moderate", "Accrual Risk"}
    assert set(out["capex_label"].dropna()) <= {"Asset Light", "Moderate", "Capital Intensive"}


def test_distress_alerts_match_flag(result):
    out, alerts = result
    assert set(alerts["company_id"]) == set(out.loc[out["distress_flag"], "company_id"])
    assert (alerts["cfo_cr"] < 0).all() and (alerts["cff_cr"] > 0).all()


def test_pattern_changes_and_distribution():
    pat = R.load_patterns()
    chg = R.changes(pat)
    assert (chg["from_pattern"] != chg["to_pattern"]).all()
    _, dist = R.distribution(pat)
    assert list(dist["pattern"]) == R.PATTERNS and len(dist) == 8
