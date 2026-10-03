# Project Deliverables Tracker (corrected, verified against the uploaded archives)

| ID | Sprint | Deliverable | Location | Status / note |
|----|--------|-------------|----------|---------------|
| D-01..D-04 | 1 | nifty100.db, load_audit.csv, validation_failures.csv, exploratory_queries.sql | data/, output/, notebooks/ | Done |
| D-05, D-06 | 2 | financial_ratios table, capital_allocation.csv | data/nifty100.db, output/ | Done |
| D-07..D-09 | 3 | screener_output.xlsx, screener_config.yaml, peer_comparison.xlsx | output/, config/ | Done |
| D-10 | 3 | 92 radar charts | reports/radar_charts/ | Done (92; stale BAJAJ-AUTO file removed) |
| D-11 | 4 | Streamlit dashboard, 8 screens | src/dashboard/app.py | Done (SIMULATED labels added) |
| D-12 | 4 | valuation_summary.xlsx | output/ | Done (SIMULATED notice sheet + header comments) |
| D-13..D-15 | 5 | cashflow_intelligence.xlsx, pros_cons_generated.csv, analysis_parsed.csv | output/ | Done |
| D-16 | 5 | Company tearsheets | reports/tearsheets/ | **91 of 92** - JIOFIN skipped by design (only 2 years of data, min 3); documented in output/skipped_tearsheets.csv. Needs your sign-off. |
| D-17 | 5 | Sector reports | reports/sector/ | **10, not 11** - the data has 10 broad sectors (11 is the number of peer groups). Needs your decision. |
| D-18 | 5 | Portfolio summary PDF | reports/portfolio/ | Done (92 pages) |
| D-19 | 6 | cluster_labels.csv | output/ | Done |
| D-20 | 6 | FastAPI server | src/api/main.py | Done - **17 endpoints** (spec said 16) |
| D-21 | 6 | pytest_report.html | reports/ | 197 passed earlier; **re-run `make test` to regenerate after these changes** |
| D-22, D-23 | 6 | analyst_guide.pdf, acceptance_checklist.pdf | docs/ | Done |
