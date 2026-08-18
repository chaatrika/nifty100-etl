import os
import sqlite3
import pandas as pd
import pytest
from src.etl.loader import initialize_database
from src.etl.reporter import generate_financial_summary_report, generate_cashflow_report, export_all_reports

@pytest.fixture
def populated_db(tmp_path):
    db_file = tmp_path / "test_nifty.db"
    
    # Initialize schema and views
    initialize_database(db_path=str(db_file))
    
    # Insert test company and financials
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO companies (company_id, ticker, company_name) VALUES (1, 'TEST', 'Test Corp');")
    cursor.execute("INSERT INTO profitandloss (company_id, year, sales, net_profit) VALUES (1, '2024', 1000, 200);")
    cursor.execute("INSERT INTO balancesheet (company_id, year, equity_capital, reserves, borrowings) VALUES (1, '2024', 100, 400, 100);")
    cursor.execute("INSERT INTO cashflow (company_id, year, operating_cash_flow, investing_cash_flow, financing_cash_flow) VALUES (1, '2024', 300, -100, -50);")
    conn.commit()
    conn.close()
    
    return str(db_file)

def test_generate_financial_summary_report(populated_db):
    df = generate_financial_summary_report(db_path=populated_db)
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "TEST"
    assert df.iloc[0]["net_profit_margin_pct"] == 20.0
    assert df.iloc[0]["roe_pct"] == 40.0

def test_generate_cashflow_report(populated_db):
    df = generate_cashflow_report(db_path=populated_db)
    assert len(df) == 1
    assert df.iloc[0]["free_cash_flow"] == 200.0

def test_export_all_reports(populated_db, tmp_path, monkeypatch):
    output_folder = tmp_path / "test_output"
    monkeypatch.setattr("src.etl.reporter.DB_PATH", populated_db)
    
    export_all_reports(output_dir=str(output_folder))
    
    assert (output_folder / "financial_ratios_report.csv").exists()
    assert (output_folder / "cashflow_summary_report.csv").exists()
    assert (output_folder / "nifty100_financial_analytics.xlsx").exists()