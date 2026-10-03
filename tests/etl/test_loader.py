# 10 unit tests for loader.py - checks row counts and column names after a load
# (Sprint 6, Day 41). These read the ALREADY LOADED database, so run `make load` first
# if you want a completely fresh check.
import os
import sqlite3

import pytest

DB_PATH = os.path.join("data", "nifty100.db")
DB_EXISTS = os.path.exists(DB_PATH)

pytestmark = pytest.mark.skipif(
    not DB_EXISTS, reason="database not found - run make load first"
)


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(DB_PATH)
    yield c
    c.close()


def test_companies_table_has_92_rows(conn):
    assert conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 92


def test_profitandloss_columns(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(profitandloss)")]
    for expected in ("company_id", "year", "sales", "net_profit", "eps"):
        assert expected in cols


def test_balancesheet_columns(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(balancesheet)")]
    for expected in ("company_id", "year", "equity_capital", "reserves", "borrowings"):
        assert expected in cols


def test_cashflow_columns(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(cashflow)")]
    for expected in (
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
    ):
        assert expected in cols


def test_no_duplicate_company_year_in_profitandloss(conn):
    dup = conn.execute(
        "SELECT COUNT(*) FROM (SELECT company_id, year, COUNT(*) c "
        "FROM profitandloss GROUP BY 1, 2 HAVING c > 1)"
    ).fetchone()[0]
    assert dup == 0


def test_no_duplicate_company_year_in_balancesheet(conn):
    dup = conn.execute(
        "SELECT COUNT(*) FROM (SELECT company_id, year, COUNT(*) c "
        "FROM balancesheet GROUP BY 1, 2 HAVING c > 1)"
    ).fetchone()[0]
    assert dup == 0


def test_foreign_keys_are_clean(conn):
    conn.execute("PRAGMA foreign_keys = ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert len(violations) == 0


def test_stock_prices_row_count_is_5520(conn):
    assert conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0] == 5520


def test_sectors_covers_all_companies(conn):
    n = conn.execute("SELECT COUNT(DISTINCT company_id) FROM sectors").fetchone()[0]
    assert n == 92


def test_year_values_are_yyyy_mm_format(conn):
    bad = conn.execute(
        "SELECT COUNT(*) FROM profitandloss WHERE year NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'"
    ).fetchone()[0]
    assert bad == 0
