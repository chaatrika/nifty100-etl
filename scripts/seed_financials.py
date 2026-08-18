import sqlite3
import pandas as pd

DB_PATH = "nifty100.db"

def seed_financial_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get company mapping
    companies = pd.read_sql_query("SELECT company_id, ticker FROM companies", conn)
    ticker_map = dict(zip(companies["ticker"], companies["company_id"]))

    if "TCS" not in ticker_map:
        print("Please run main loader first to seed company records.")
        return

    tcs_id = ticker_map["TCS"]
    reliance_id = ticker_map.get("RELIANCE", ticker_map.get("RELIANCENS"))

    # 1. Seed Profit & Loss
    pnl_data = [
        (tcs_id, "2024", 240893, 190000, 45908),
        (reliance_id, "2024", 900000, 750000, 69624)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO profitandloss (company_id, year, sales, expenses, net_profit)
        VALUES (?, ?, ?, ?, ?)
    """, pnl_data)

    # 2. Seed Balance Sheet (Columns matching schema.sql)
    bs_data = [
        (tcs_id, "2024", 370, 90000, 0, 120000),
        (reliance_id, "2024", 6765, 400000, 300000, 800000)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO balancesheet (company_id, year, equity_capital, reserves, borrowings, total_assets)
        VALUES (?, ?, ?, ?, ?, ?)
    """, bs_data)

    # 3. Seed Cash Flow
    cf_data = [
        (tcs_id, "2024", 44000, -5000, -38000),
        (reliance_id, "2024", 130000, -90000, -35000)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO cashflow (company_id, year, operating_cash_flow, investing_cash_flow, financing_cash_flow)
        VALUES (?, ?, ?, ?, ?)
    """, cf_data)

    conn.commit()
    conn.close()
    print("Financial data successfully seeded.")

if __name__ == "__main__":
    seed_financial_data()