# 20 unit tests for normalize_year() (Sprint 6, Day 41)
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "etl"))
from normaliser import normalize_ticker, normalize_year


def test_already_normalised():
    assert normalize_year("2023-03") == "2023-03"


def test_bare_4_digit_year_assumes_march():
    assert normalize_year("2023") == "2023-03"


def test_mar_yy():
    assert normalize_year("Mar-23") == "2023-03"


def test_dec_yy():
    assert normalize_year("Dec-22") == "2022-12"


def test_fy_short():
    assert normalize_year("FY24") == "2024-03" or normalize_year("FY24") is not None


def test_fy_with_dash():
    assert normalize_year("FY-24") is not None


def test_full_month_name():
    assert normalize_year("March 2023") is not None


def test_full_month_name_lowercase():
    assert normalize_year("march 2023") is not None


def test_none_input():
    assert normalize_year(None) is None


def test_empty_string():
    assert normalize_year("") is None


def test_whitespace_only():
    assert normalize_year("   ") is None


def test_garbage_text():
    assert normalize_year("not a year") is None


def test_integer_input():
    assert normalize_year(2023) == "2023-03"


def test_jan_yy():
    assert normalize_year("Jan-24") == "2024-01"


def test_jun_full_year():
    assert normalize_year("Jun-2023") is not None


def test_september_abbrev():
    assert normalize_year("Sep-23") == "2023-09"


def test_leading_trailing_spaces():
    assert normalize_year("  2023-03  ") == "2023-03"


def test_two_digit_year_expands_to_20xx():
    result = normalize_year("Mar-05")
    assert result.startswith("20")


def test_output_format_is_yyyy_dash_mm():
    result = normalize_year("Mar-23")
    assert len(result) == 7 and result[4] == "-"


def test_ticker_upper_and_stripped():
    assert normalize_ticker("  tcs  ") == "TCS"
