import sqlite3

# ==========================================
# 1. CORE RATIO ENGINE & LOGIC
# ==========================================

def calculate_all_metrics(sales, net_profit, equity, reserves, borrowings, 
                          interest, cfo, cfi, cff, start_sales_5yr, sector):
    total_equity = equity + reserves

    # Profitability & Leverage
    npm = (net_profit / sales * 100) if sales > 0 else None
    roe = (net_profit / total_equity * 100) if total_equity > 0 else None
    de_ratio = 0.0 if borrowings == 0 else ((borrowings / total_equity) if total_equity > 0 else None)
    
    # Interest Coverage Ratio (ICR)
    if not interest:
        icr, icr_label = None, "Debt Free"
    else:
        icr = net_profit / interest
        icr_label = "Low Coverage" if icr < 1.5 else "Normal"

    # 5-Year CAGR Engine & Edge Cases
    if not start_sales_5yr or not sales:
        cagr_5yr, cagr_flag = None, "INSUFFICIENT"
    elif start_sales_5yr == 0:
        cagr_5yr, cagr_flag = None, "ZERO_BASE"
    elif start_sales_5yr > 0 and sales > 0:
        cagr_5yr, cagr_flag = round(((sales / start_sales_5yr) ** 0.2 - 1) * 100, 2), "NORMAL"
    elif start_sales_5yr > 0 and sales < 0:
        cagr_5yr, cagr_flag = None, "DECLINE_TO_LOSS"
    elif start_sales_5yr < 0 and sales > 0:
        cagr_5yr, cagr_flag = None, "TURNAROUND"
    else:
        cagr_5yr, cagr_flag = None, "BOTH_NEGATIVE"

    # Cash Flow & Capital Allocation Classifier
    fcf = (cfo or 0) + (cfi or 0)
    signs = ("+" if (cfo or 0) >= 0 else "-", "+" if (cfi or 0) >= 0 else "-", "+" if (cff or 0) >= 0 else "-")
    patterns = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue"
    }

    return (npm, roe, de_ratio, icr, icr_label, cagr_5yr, cagr_flag, fcf, patterns.get(signs, "Mixed"))


# ==========================================
# 2. DATABASE PIPELINE & VERIFICATION
# ==========================================

def run_pipeline():
    conn = sqlite3.connect("nifty100.db")
    cursor = conn.cursor()

    # Drop old table to reset table schema (Fixes column mismatch errors)
    cursor.execute("DROP TABLE IF EXISTS financial_ratios;")

    # Create table schema with 11 columns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_ratios (
        company_id INT, year INT, npm REAL, roe REAL, de_ratio REAL, 
        icr REAL, icr_label TEXT, cagr_5yr REAL, cagr_flag TEXT, 
        fcf REAL, pattern_label TEXT, PRIMARY KEY (company_id, year)
    )""")

    # Sample dataset representing processed raw data
    sample_dataset = [
        {"id": 1, "year": 2024, "sector": "IT", "sales": 1000, "pat": 150, "equity": 500, "reserves": 300, "borrowings": 0, "interest": 0, "cfo": 200, "cfi": -50, "cff": -30, "sales_5yr_ago": 600},
        {"id": 2, "year": 2024, "sector": "Financials", "sales": 2000, "pat": 300, "equity": 100, "reserves": 100, "borrowings": 1200, "interest": 50, "cfo": 100, "cfi": 20, "cff": -10, "sales_5yr_ago": 1000}
    ]

    for c in sample_dataset:
        metrics = calculate_all_metrics(
            c["sales"], c["pat"], c["equity"], c["reserves"], c["borrowings"],
            c["interest"], c["cfo"], c["cfi"], c["cff"], c["sales_5yr_ago"], c["sector"]
        )
        cursor.execute(
            "INSERT OR REPLACE INTO financial_ratios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (c["id"], c["year"], *metrics)
        )

    conn.commit()

    # Exit Verification Checks
    cursor.execute("SELECT COUNT(*) FROM financial_ratios")
    print(f"Total Rows Populated: {cursor.fetchone()[0]}")

    cursor.execute("SELECT company_id, roe, de_ratio FROM financial_ratios WHERE roe > 15 AND de_ratio < 1")
    print(f"Screener Matches (ROE > 15%, D/E < 1): {len(cursor.fetchall())}")

    conn.close()

if __name__ == "__main__":
    run_pipeline()