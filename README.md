# Nifty 100 Financial ETL Pipeline

A production-ready Python ETL (Extract, Transform, Load) pipeline that ingests financial statements, normalizes data structures, loads relational models into SQLite, computes key financial ratios via database views, and exports multi-format analytical deliverables.

## Project Structure

```text
nifty100-etl/
├── db/                     # Database schemas and initialization scripts
├── output/                 # Generated CSV and Excel deliverables
├── scripts/                # Utility and database seeding scripts
│   └── seed_financials.py  # Populates financial statements
├── src/                    # Source ETL modules
│   └── etl/
│       ├── loader.py       # Database connection & schema management
│       ├── normaliser.py   # Data cleaning and field standardization
│       ├── reporter.py     # CSV and Excel report generators
│       └── validator.py    # Schema & financial logic validation
├── tests/                  # Unit and integration tests
│   └── etl/                # Test suites for ETL modules
├── main.py                 # Pipeline CLI entrypoint
├── nifty100.db             # SQLite database instance
└── requirements.txt        # Project dependencies