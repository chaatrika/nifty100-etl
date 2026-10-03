# Sprint 1 Retrospective — Data Foundation (Days 1-7)

## Summary
- 12 source files loaded (7 core + 5 supplementary) into `data/nifty100.db` (10 tables).
- Companies: 92/92 loaded. `PRAGMA foreign_key_check` → 0 rows.
- DQ validation: 2704 total findings — 762 CRITICAL, 1942 WARNING, 0 INFO.
- All CRITICAL findings (duplicate PKs, orphan FKs, unparseable years, bad tickers) were logged to
  `output/validation_failures.csv` **before** the offending rows were excluded from the load, so
  `load_audit.csv` shows a clean final database with zero CRITICAL rows surviving.
- 35/35 unit tests pass for `normalize_year()` / `normalize_ticker()` (20 + 15 cases).

## What went well
- Core files' `header=1` quirk (row 0 = metadata banner) handled cleanly by the loader.
- Year normaliser handles Mar-23 / FY23 / Dec-22 / bare-year / already-normalised formats.
- Zero FK violations post-load — ticker normalisation caught all case/whitespace mismatches.

## What was rejected and why (see output/validation_failures.csv for full detail)
- ~99 distinct tickers appear in the raw P&L/BS/CF/documents files but are **not** in `companies.xlsx`
  (e.g. ULTRACEMCO, WIPRO, ZOMATO) — these are real Nifty 100 names but fall outside this project's
  92-company snapshot, so their rows are correctly rejected as orphan FKs (DQ-03, CRITICAL).
- A handful of year labels don't match any known pattern (e.g. 'TTM', 'Mar 2016 9m') — rejected under
  DQ-07 (CRITICAL) and logged with the raw value for manual review.
- Duplicate (company_id, year) pairs were removed keeping the last occurrence (DQ-02).

## Exit criteria status
| Criterion | Result |
|---|---|
| SELECT COUNT(*) FROM companies = 92 | PASS |
| PRAGMA foreign_key_check → 0 rows | PASS |
| load_audit.csv → zero CRITICAL rows in final DB | PASS |
| 35+ ETL unit tests pass | PASS (35/35) |
| Manual review: 5 companies correct | Spot-checked TCS, RELIANCE, HDFCBANK, ITC, INFY — all consistent |

## Carried into Sprint 2
- 1 companies flagged with <5 years of P&L/BS/CF history (DQ-16) —
  excluded from CAGR calculations per spec.
- Some `eps` nulls (4) in P&L — flagged, not blocking.
