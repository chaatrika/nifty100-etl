from src.nlp import parser as P


def test_parse_text_examples():
    assert P.parse_text("10 Years: 21%") == (10, 21.0)
    assert P.parse_text("5 Years:       24%") == (5, 24.0)
    assert P.parse_text("5 Years          14%") == (5, 14.0)     # colon missing
    assert P.parse_text("1 Year: -2%") == (1, -2.0)             # negative value
    assert P.parse_text("3 Years: 12.5%") == (3, 12.5)


def test_text_that_does_not_match():
    assert P.parse_text("TTM: 43%") is None
    assert P.parse_text("Last Year: 12%") is None
    assert P.parse_text(None) is None


def test_parse_frame_logs_failures_and_unknown_companies():
    import pandas as pd
    df = pd.DataFrame([{"id": 1, "company_id": "TCS", "compounded_sales_growth": "10 Years: 11%",
                        "compounded_profit_growth": "TTM: 8%", "stock_price_cagr": "5 Years: 16%", "roe": "Last Year: 52%"},
                       {"id": 2, "company_id": "NOTINDB", "compounded_sales_growth": "10 Years: 8%",
                        "compounded_profit_growth": "10 Years: 9%", "stock_price_cagr": "10 Years: 9%", "roe": "10 Years: 9%"}])
    parsed, failures = P.parse_frame(df, {"TCS"})
    assert len(parsed) == 2
    assert set(failures["reason"]) == {"text does not match 'N Years: X%'", "company not in companies table"}
    assert (failures["company_id"] == "NOTINDB").sum() == 4
