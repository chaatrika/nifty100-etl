# Nifty 100 Financial Intelligence Platform

Data platform for fundamental analysis of 92 Nifty 100 companies: ETL, a
50+ KPI ratio engine, an investment screener, financial health scoring,
sector/peer analytics, and reporting. See
`Nifty100_Project_Document_FINAL.pdf` for the full spec.

## Directory structure

```
nifty100/
├── data/
│   ├── raw/                 7 core Excel files (companies, profitandloss, balancesheet,
│   │                        cashflow, analysis, documents, prosandcons). READ-ONLY — source of truth.
│   ├── supporting/          5 supplementary Excel files (sectors, stock_prices, market_cap,
│   │                        financial_ratios, peer_groups).
│   └── nifty100.db          Generated SQLite database — rebuild anytime with `make load`.
│
├── src/
│   ├── etl/                 loader.py, normaliser.py, validator.py            [Sprint 1 — done]
│   ├── analytics/           ratios.py, cagr.py, cashflow_kpis.py, screener/, peer.py, clustering.py
│   ├── nlp/                 parser.py, pros_cons_generator.py                 [Sprint 5]
│   ├── dashboard/           app.py, pages/, utils/                            [Sprint 4]
│   ├── api/                 main.py, routers/                                 [Sprint 6]
│   └── reports/             tearsheet.py, sector_report.py, portfolio_report.py [Sprint 5]
│
├── tests/
│   ├── etl/                 test_normalise.py                                 [Sprint 1 — done, 35/35 passing]
│   ├── kpi/                 KPI formula tests                                 [Sprint 2]
│   ├── api/                 API endpoint tests                                [Sprint 6]
│   └── dq/                  DQ rule tests                                     [Sprint 3]
│
├── db/
│   └── schema.sql           10-table SQLite schema with FK constraints
│
├── notebooks/
│   └── exploratory_queries.sql  10 exploratory SQL queries
│
├── output/                  Generated audit artifacts (load_audit.csv, validation_failures.csv, retros)
├── config/                  .env.template, screener_config.yaml (Sprint 3+)
├── reports/                 tearsheets/, sector/, portfolio/, radar_charts/ (generated, Sprint 5+)
├── Makefile
├── .gitignore
└── README.md
```

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pandas openpyxl pytest

cp config/.env.template .env       # edit if needed

make load                          # builds data/nifty100.db from data/raw + data/supporting
make test                          # runs the unit test suite
```

## Status

- **Sprint 1 — Data Foundation:** done. `nifty100.db` built (10 tables, 92 companies,
  0 FK violations). See `output/sprint1_retro.md` for details on what was rejected and why.
- **Sprint 2–6:** not started. Directory skeleton (`src/analytics/`, `src/dashboard/`, etc.)
  is in place, ready to fill in.

---

## Sprint 4 - Streamlit dashboard and valuation

### Run the dashboard
From the project root (the folder that has `data/` and `src/`):

```
pip install -r requirements.txt
python -m src.analytics.valuation      # makes output/valuation_summary.xlsx and valuation_flags.csv
streamlit run src/dashboard/app.py     # opens http://localhost:8501
```

### The 8 screens
| # | Screen | What it shows |
|---|--------|---------------|
| 1 | Home | 6 KPI tiles, sector donut, top 5 by composite score. Year selector (2019-2024) in the sidebar. |
| 2 | Company Profile | Search box, company card, 6 KPI tiles, revenue/profit bars, ROE/ROCE lines, pros and cons. |
| 3 | Screener | 10 sliders, 6 preset buttons, live results table, result count, CSV download. Uses the same engine as the Excel screener. |
| 4 | Peer Comparison | Peer group dropdown, radar (company vs group average percentile), side-by-side KPI table with the benchmark highlighted. |
| 5 | Trend Analysis | Up to 3 metrics over 10 years, YoY % labels on each point. |
| 6 | Sector Analysis | Bubble chart (revenue vs ROE, size = market cap) and sector median KPI bars. |
| 7 | Capital Allocation | Treemap of companies by capital allocation pattern, plus a pattern dropdown that lists the companies. |
| 8 | Annual Reports | BSE report links by year. "Check which links are still live" marks 404 links as "Report unavailable". |

### Notes / decisions
- A slider that sits at its extreme end (the loosest value) means "filter off". Presets fill the sliders; preset filters that have no slider (e.g. dividend payout max) are applied too and shown above the table.
- Missing values show as N/A. Fewer than 10 years of data shows a "Data available for N year(s)" note.
- Valuation flag: P/E above sector median x 1.5 = Caution, below x 0.7 = Discount, otherwise Fair. Companies with no usable P/E or sector median get N/A.
- Data changes are cached for 10 minutes (`@st.cache_data(ttl=600)`).
- Tests: `python -m pytest tests/ -q` (includes dashboard smoke tests).

---

## Sprint 5 - NLP, cash flow intelligence and PDF reports

Run from the project root, in this order (each step needs the ones above it):

```
python -m src.nlp.parser                         # output/analysis_parsed.csv, parse_failures.csv, analysis_crosscheck.csv
python -m src.nlp.pros_cons_generator            # output/pros_cons_generated.csv
python -m src.analytics.cashflow_intelligence    # output/cashflow_intelligence.xlsx, distress_alerts.csv
python -m src.analytics.capital_report           # pattern_distribution.csv, pattern_changes.csv, capital_allocation_gaps.csv
python -m src.reports.tearsheet                  # reports/tearsheets/<TICKER>_tearsheet.pdf  (2 pages each)
python -m src.reports.sector_report              # reports/sector/<Sector>_report.pdf
python -m src.reports.portfolio                  # reports/portfolio/portfolio_summary.pdf
```

One tearsheet only: `python -m src.reports.tearsheet TCS`.

### Notes / decisions
- Pros and cons: 12 pro rules and 12 con rules. Confidence = 50 + 50 x signal strength, and only lines above 60 are written.
  Rules that need a "non-financial" company (D/E, interest coverage, ROCE, net debt) skip banks/insurers/NBFCs.
- Pro Rule 11 follows its text (profit growing faster than revenue). The rule title in the plan says the opposite.
- A strong company can trigger no con rule (and a weak one no pro rule). So that every company has at least 1 pro and 1 con,
  we add one relative line (rule id `PRO_REL` / `CON_REL`) comparing the company with the Nifty 100 median.
  Companies with no pro at all get a plain "profitable in the latest year" line at confidence 62.
- ROE above 150% (tiny equity base, e.g. BEL, HAL, INDIGO) is not used by the ROE rules.
- Tearsheets are made for all 92 companies; a company with no profit and loss data would be skipped and listed in output/skipped_tearsheets.csv. Companies with under 3 years of data (JIOFIN) get a limited-history note.
- 11 sector PDFs: the 10 broad sectors in the database plus a cross-cutting "Conglomerates / Other" report. All 92 companies get a tearsheet (JIOFIN carries a limited-history note).

## Sprint 6 - Clustering, REST API, testing and sign-off

### Run the clustering and analysis
```
python -m src.analytics.clustering      # cluster_labels.csv, elbow_plot.png, correlation_heatmap.png, portfolio_stats.csv, outlier_report.csv
```

### Run the API
```
uvicorn src.api.main:app --port 8000
```
Interactive docs: http://localhost:8000/docs. All 16 endpoints are documented there and in `docs/openapi.json`
(a ready-to-import Postman collection is at `docs/postman_collection.json`).

The dashboard (`streamlit run src/dashboard/app.py`, port 8501) and the API (port 8000) can run at the same time -
they use different ports and do not conflict.

### Run the full test suite
```
python -m pytest tests/ -q
python -m pytest tests/ --html=reports/pytest_report.html --self-contained-html -q
```

### Final sign-off
```
python -m src.reports.analyst_guide          # docs/analyst_guide.pdf (10+ pages)
python -m src.reports.acceptance_check        # runs all 20 acceptance gates -> output/acceptance_gates.csv
python -m src.reports.acceptance_checklist    # docs/acceptance_checklist.pdf (23 deliverables)
```

### Notes / known issues from Sprint 6
- **Clusters are uneven** (60 of 92 companies land in one cluster). This follows from the small number of
  extreme outliers (BEL, HAL, INDIGO, etc. - see `output/outlier_report.csv`) pulling the KMeans centroids.
  Worth reviewing with the team lead before presenting the 5 archetype names as final.
- **Sector count is 10, not 11.** Several planning documents (and one dashboard label) assumed 11 broad
  sectors; the data has 10. Tests and the API were corrected to expect 10.
- **JIOFIN has no tearsheet** (only 2 years of data, below the Day 33 minimum of 3) - logged in
  `output/skipped_tearsheets.csv`, so 91 of 92 tearsheets exist, not 92.
- **AC-13** (API screener vs `screener_output.xlsx`) compares different filter combinations by design (query
  params vs a named preset), so it checks for large overlap rather than an exact match.
