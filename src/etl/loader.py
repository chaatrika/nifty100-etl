import os
import sqlite3
import pandas as pd
from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import validate_null_values, validate_financial_integrity

DB_PATH = "nifty100.db"
SCHEMA_PATH = "db/schema.sql"
VIEWS_PATH = "db/views.sql"
AUDIT_LOG_PATH = "output/load_audit.csv"
FAILURES_LOG_PATH = "output/validation_failures.csv"

def initialize_database(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH, views_path: str = VIEWS_PATH):
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r', encoding='utf-8-sig') as f:
        conn.executescript(f.read())
    
    if os.path.exists(views_path):
        with open(views_path, 'r', encoding='utf-8-sig') as f:
            conn.executescript(f.read())
            
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.close()

def log_audit_trail(table_name: str, records_processed: int, status: str):
    os.makedirs("output", exist_ok=True)
    audit_df = pd.DataFrame([{
        "table_name": table_name,
        "records_processed": records_processed,
        "status": status
    }])
    header_needed = not os.path.exists(AUDIT_LOG_PATH)
    audit_df.to_csv(AUDIT_LOG_PATH, mode='a', index=False, header=header_needed)

def log_validation_failures(failures: list[dict]):
    if not failures:
        return
    os.makedirs("output", exist_ok=True)
    df_failures = pd.DataFrame(failures)
    header_needed = not os.path.exists(FAILURES_LOG_PATH)
    df_failures.to_csv(FAILURES_LOG_PATH, mode='a', index=False, header=header_needed)

def load_sample_companies(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    
    raw_data = pd.DataFrame([
        {"ticker": " tcs ", "company_name": "Tata Consultancy Services"},
        {"ticker": "RELIANCE.NS", "company_name": "Reliance Industries"},
        {"ticker": "INFY", "company_name": "Infosys Limited"}
    ])

    raw_data["ticker"] = raw_data["ticker"].apply(normalize_ticker)

    existing_tickers = pd.read_sql_query("SELECT ticker FROM companies", conn)["ticker"].tolist()
    new_data = raw_data[~raw_data["ticker"].isin(existing_tickers)]

    if not new_data.empty:
        failures = validate_null_values(new_data, ["ticker", "company_name"], "companies")
        log_validation_failures(failures)

        new_data.to_sql("companies", conn, if_exists="append", index=False)
        records_loaded = len(new_data)
    else:
        records_loaded = 0

    conn.close()

    log_audit_trail("companies", records_loaded, "SUCCESS")
    print(f"Loaded {records_loaded} new records into 'companies'.")

def main():
    print("Initializing Database with Schema and Views...")
    initialize_database()
    log_audit_trail("schema_init", 0, "SUCCESS")
    
    print("Running Ingestion Pipeline...")
    load_sample_companies()
    print("ETL Ingestion Run Complete.")

if __name__ == "__main__":
    main()