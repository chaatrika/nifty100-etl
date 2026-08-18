import os
import sqlite3
import pandas as pd

DB_PATH = "nifty100.db"
OUTPUT_DIR = "output"

def generate_financial_summary_report(db_path: str = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    query = """
    SELECT 
        ticker,
        company_name,
        year,
        sales,
        net_profit,
        net_profit_margin_pct,
        roe_pct,
        debt_to_equity
    FROM v_financial_ratios
    ORDER BY roe_pct DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def generate_cashflow_report(db_path: str = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    query = """
    SELECT 
        ticker,
        company_name,
        year,
        operating_cash_flow,
        investing_cash_flow,
        financing_cash_flow,
        free_cash_flow
    FROM v_cashflow_summary
    ORDER BY free_cash_flow DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def export_all_reports(output_dir: str = OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Fetch dataframes
    df_ratios = generate_financial_summary_report()
    df_cashflow = generate_cashflow_report()

    # 2. Export individual CSVs
    ratios_csv = os.path.join(output_dir, "financial_ratios_report.csv")
    cashflow_csv = os.path.join(output_dir, "cashflow_summary_report.csv")
    
    df_ratios.to_csv(ratios_csv, index=False)
    df_cashflow.to_csv(cashflow_csv, index=False)
    
    print(f"Exported CSV: {ratios_csv}")
    print(f"Exported CSV: {cashflow_csv}")

    # 3. Export multi-tab Excel Workbook
    excel_path = os.path.join(output_dir, "nifty100_financial_analytics.xlsx")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_ratios.to_excel(writer, sheet_name="Financial Ratios", index=False)
        df_cashflow.to_excel(writer, sheet_name="Cash Flow Summary", index=False)
        
    print(f"Exported Excel Workbook: {excel_path}")

if __name__ == "__main__":
    export_all_reports()