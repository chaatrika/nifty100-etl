import pandas as pd
import pytest

from src.nlp import pros_cons_generator as G


@pytest.fixture(scope="module")
def out():
    return G.generate()


def test_every_company_has_a_pro_and_a_con(out):
    from src.analytics import series
    ids = series.load_all()["companies"]["company_id"]
    no_pro, no_con = G.coverage(out, ids)
    assert no_pro == [] and no_con == []


def test_columns_and_confidence(out):
    assert list(out.columns) == ["company_id", "type", "rule_id", "text", "confidence_pct"]
    assert set(out["type"]) == {"pro", "con"}
    assert (out["confidence_pct"] > 60).all() and (out["confidence_pct"] <= 100).all()


def test_helpers():
    assert G.trailing_streak([1, -1, 2, 3, 4], lambda v: v > 0) == 3
    assert G.strictly([1, 2, 3], "up") and not G.strictly([1, 3, 2], "up")
    assert G.confidence(0) == 50 and G.confidence(1) == 100 and G.confidence(5) == 100


def _company(**kw):
    ratios = pd.DataFrame(kw.get("ratios", {"fy": [2024]}))
    return G.Company("X", kw.get("sector", "Industrials"), ratios, pd.DataFrame(kw.get("pl", {"fy": []})),
                     pd.DataFrame(kw.get("bs", {"fy": []})), pd.DataFrame())


def test_pro1_needs_three_years_above_20():
    c = _company(ratios={"fy": [2022, 2023, 2024], "return_on_equity_pct": [25, 30, 28]})
    assert G.pro1(c) is not None
    c = _company(ratios={"fy": [2022, 2023, 2024], "return_on_equity_pct": [25, 15, 28]})
    assert G.pro1(c) is None


def test_con1_skips_financials_and_fills_in_value():
    r = {"fy": [2024], "debt_to_equity": [3.5]}
    assert G.con1(_company(ratios=r, sector="Financials")) is None
    assert "3.50" in G.con1(_company(ratios=r))[1]


def test_pro11_follows_the_text_not_the_title():
    # profit growing faster than revenue = operating leverage
    c = _company(ratios={"fy": [2024], "revenue_cagr_5yr": [10.0], "pat_cagr_5yr": [18.0]})
    assert G.pro11(c) is not None
    c = _company(ratios={"fy": [2024], "revenue_cagr_5yr": [18.0], "pat_cagr_5yr": [10.0]})
    assert G.pro11(c) is None
