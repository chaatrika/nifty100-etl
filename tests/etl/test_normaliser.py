import pytest
from src.etl.normaliser import normalize_ticker, normalize_year

@pytest.mark.parametrize("input_val, expected", [
    ("2021", 2021), ("FY2022", 2022), ("2020-21", 2020), (2023, 2023),
    ("FY 2024", 2024), ("2019/20", 2019), ("FY-18", 2018), ("2015.0", 2015),
    ("CY2020", 2020), ("2025_Q4", 2025), ("2017AB", 2017), ("FY002016", 2016),
    ("2014-2015", 2014), ("Year: 2013", 2013), ("2012", 2012), (2011, 2011),
    ("2010", 2010), ("2009", 2009), ("2008", 2008), ("2007", 2007)
])
def test_normalize_year(input_val, expected):
    assert normalize_year(input_val) == expected

def test_normalize_year_invalid():
    with pytest.raises(ValueError):
        normalize_year("InvalidYearText")

@pytest.mark.parametrize("input_val, expected", [
    (" tcs ", "TCS"), ("RELIANCE.NS", "RELIANCENS"), ("infy", "INFY"),
    ("HDFCBANK-EQ", "HDFCBANKEQ"), (" Wipro ", "WIPRO"), ("icici_bank", "ICICIBANK"),
    ("TATAMOTORS...", "TATAMOTORS"), ("sbin", "SBIN"), ("bharti_artel", "BHARTIARTEL"),
    (" ITC ", "ITC"), ("kotak-bank", "KOTAKBANK"), ("lt_limited", "LTLIMITED"),
    ("axisbnk", "AXISBNK"), (" HCLTECH ", "HCLTECH"), ("asianpaints", "ASIANPAINTS")
])
def test_normalize_ticker(input_val, expected):
    assert normalize_ticker(input_val) == expected

def test_normalize_ticker_edge_cases():
    assert normalize_ticker("") == ""
    assert normalize_ticker(None) == ""
    assert normalize_ticker(123) == ""