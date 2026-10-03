# Tests for the peer percentile engine (Sprint 3)

import os
import sqlite3

import pandas as pd
import pytest

from src.analytics import peer as P

DB_EXISTS = os.path.exists(P.DB_PATH)


def test_percent_rank_basic():
    result = P.percent_rank([10, 20, 30, 40, 50])
    assert list(result) == [0.0, 0.25, 0.5, 0.75, 1.0]


def test_percent_rank_ties_share_lowest_rank():
    result = P.percent_rank([10, 10, 30])
    assert list(result) == [0.0, 0.0, 1.0]


def test_percent_rank_ignores_empty_values():
    result = P.percent_rank([10, None, 30])
    assert result.iloc[0] == 0.0
    assert result.iloc[2] == 1.0
    assert pd.isna(result.iloc[1])


def test_percent_rank_single_value_is_empty():
    assert P.percent_rank([5]).isna().all()


def make_test_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE peer_groups (peer_group_name TEXT, company_id TEXT, is_benchmark INTEGER)")
    conn.execute("INSERT INTO peer_groups VALUES ('IT Services', 'AAA', 1)")
    conn.execute("CREATE TABLE peer_percentiles (company_id TEXT, peer_group_name TEXT, metric TEXT, "
                 "value REAL, percentile_rank REAL, year INTEGER)")
    conn.execute("INSERT INTO peer_percentiles VALUES ('AAA', 'IT Services', 'return_on_equity_pct', 20, 1.0, 2024)")
    return conn


def test_company_without_peer_group_gets_message_not_error():
    conn = make_test_db()
    assert P.get_company_percentiles(conn, "ZZZ") == "No peer group assigned"


def test_company_with_peer_group_gets_table():
    conn = make_test_db()
    result = P.get_company_percentiles(conn, "AAA")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1


@pytest.mark.skipif(not DB_EXISTS, reason="database not found")
def test_de_percentile_is_flipped_lower_debt_is_better():
    conn = sqlite3.connect(P.DB_PATH)
    df = P.compute_peer_percentiles(conn)
    conn.close()
    de = df[(df["metric"] == "debt_to_equity") & (df["peer_group_name"] == "FMCG") & (df["year"] == 2024)]
    de = de.dropna(subset=["value"]).sort_values("value")
    # the company with the lowest D/E must have the highest percentile
    assert de.iloc[0]["percentile_rank"] == de["percentile_rank"].max()
    assert de.iloc[-1]["percentile_rank"] == de["percentile_rank"].min()


@pytest.mark.skipif(not DB_EXISTS, reason="database not found")
@pytest.mark.parametrize("group", ["IT Services", "FMCG"])
def test_highest_roe_has_highest_percentile(group):
    conn = sqlite3.connect(P.DB_PATH)
    df = P.compute_peer_percentiles(conn)
    conn.close()
    roe = df[(df["metric"] == "return_on_equity_pct") & (df["peer_group_name"] == group) & (df["year"] == 2024)]
    best = roe.sort_values("value").iloc[-1]
    assert best["percentile_rank"] == 1.0


@pytest.mark.skipif(not DB_EXISTS, reason="database not found")
def test_peer_table_covers_all_11_groups_and_10_metrics():
    conn = sqlite3.connect(P.DB_PATH)
    df = pd.read_sql("SELECT * FROM peer_percentiles", conn)
    conn.close()
    assert df["peer_group_name"].nunique() == 11
    assert df["metric"].nunique() == 10
    assert df["percentile_rank"].between(0, 1).all()
