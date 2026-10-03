# Smoke tests: every screen loads without an exception (uses Streamlit's AppTest)
import os
import sys

import pytest
from streamlit.testing.v1 import AppTest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "src", "dashboard")
sys.path.insert(0, DASH)
APP = os.path.join(DASH, "app.py")
PAGES = ["01_home", "02_profile", "03_screener", "04_peers", "05_trends", "06_sectors", "07_capital", "08_reports"]


def open_page(name):
    at = AppTest.from_file(APP, default_timeout=90)
    at.run()
    at.switch_page(f"pages/{name}.py")
    at.run()
    return at


@pytest.mark.parametrize("name", PAGES)
def test_page_loads(name):
    assert not open_page(name).exception


@pytest.mark.parametrize("ticker", ["TCS", "HDFCBANK", "HINDUNILVR", "RELIANCE", "SUNPHARMA", "JIOFIN"])
def test_ticker_screens(ticker):
    for name in ["02_profile", "05_trends", "08_reports"]:
        at = open_page(name)
        at.text_input[0].set_value(ticker).run()
        assert not at.exception


def test_unknown_ticker_message():
    at = open_page("02_profile")
    at.text_input[0].set_value("ZZZZ").run()
    assert "Ticker not found" in at.warning[0].value


def test_screener_extremes():
    for pick in ("max", "min"):
        at = open_page("03_screener")
        for s in at.sidebar.slider:
            s.set_value(s.max if pick == "max" else s.min)
        at.run()
        assert not at.exception
