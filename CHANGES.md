# Corrections applied (round 2) - tracker now matches the files

## Deliverable counts (tracker was the spec)
- D-16: 92 tearsheets. JIOFIN (2 years of data) now gets a tearsheet with a "limited history" note (tearsheet.py: MIN_YEARS=1, LIMITED_YEARS=3). Only a company with no P&L data is skipped; output/skipped_tearsheets.csv is now empty.
- D-17: 11 sector reports. The 11th, "Conglomerates / Other" (spec section 6.1), is a cross-cutting report of companies whose sub-sector contains conglomerate / holding / diversified (7 companies: ADANIENT, BAJAJFINSV, BAJAJHLDNG, GRASIM, ITC, JIOFIN, RELIANCE). They also stay in their own broad-sector reports. The database and API still have 10 broad sectors (tests/api/test_sectors.py unchanged).
  NOTE: the spec says this group has 5 companies; the database labels do not map exactly, so the group is rule-based (OTHER_KEYWORDS in sector_report.py) - edit that tuple to change membership.

## Earlier fixes (round 1, still included)
SIMULATED labels in dashboard, sector/tearsheet/portfolio PDFs, API market-cap response; `make api`, `make report`; `make test` writes reports/pytest_report.html; requirements.txt gained fastapi, uvicorn, httpx, pytest-html.

## Also updated
analyst_guide.py (uppercase SIMULATED, new tearsheet/sector wording) and regenerated docs/analyst_guide.pdf + docs/acceptance_checklist.pdf; README; tests/reports/test_reports.py (JIOFIN now gets a tearsheet, unknown ticker skipped, 11 sector reports); acceptance_gates.csv AC-17 detail.

## Still required on your machine
Run `make test` (pytest, streamlit and fastapi were not installable here). It regenerates reports/pytest_report.html (D-21) and must show 0 failures before the Git commit. I ran the report tests by hand (all pass), but not the full 200-test suite.
Caution: the tearsheet tests call run_batch, which rewrites output/skipped_tearsheets.csv; after `make test`, run `python -m src.reports.tearsheet` once to restore it.
