import sys
from src.etl.loader import initialize_database
from scripts.seed_financials import seed_financial_data
from src.etl.reporter import export_all_reports

def main():
    print("==========================================")
    print("Starting Nifty 100 Financial ETL Pipeline")
    print("==========================================")
    
    # 1. Initialize schema and database views
    print("\n[1/3] Initializing Database Schema...")
    initialize_database()
    
    # 2. Execute financial seeding / loading
    print("\n[2/3] Seeding Financial Data...")
    seed_financial_data()
    
    # 3. Export financial reports
    print("\n[3/3] Generating Financial Analytics Deliverables...")
    export_all_reports()
    
    print("\n==========================================")
    print("Pipeline Execution Completed Successfully!")
    print("==========================================")

if __name__ == "__main__":
    main()