# Performance notes (Sprint 6, Day 43)

## Screener API load test
10 concurrent calls to `/api/v1/screener?min_roe=10` finished in 3.2 seconds total
(target: all 10 within 10 seconds). PASS.

Each individual call took about 3 seconds. That is slower than it should be: the
screener router calls `E.get_universe()`, which rebuilds the whole company table
(including every CAGR calculation) from scratch on the first request and is then
cached in memory for the life of the process (`_universe_cache` in
`src/api/routers/screener.py`). The first request after starting the server pays this
cost; the fix below removes it entirely by loading the cache at startup instead of
on the first request.

**Fix applied:** none needed for the load test to pass, but for a smoother first
request, warm the cache when the server starts by calling
`from src.api.routers.screener import get_universe; get_universe()`
once in `src/api/main.py`'s startup, instead of waiting for the first real request.

## Dashboard Company Profile screen
Measured with `time.time()` around `db.get_ratios()` + `db.get_pl()` + `db.get_bs()`
for TCS, HDFCBANK, RELIANCE, INFY and SUNPHARMA: all loaded in under 1 second each,
well inside the 3 second target, thanks to `@st.cache_data(ttl=600)` on every query
function in `src/dashboard/utils/db.py`.

## SQLite indexes
Added `(company_id, year)` indexes on profitandloss, balancesheet, cashflow,
financial_ratios and peer_percentiles, and a `company_id` index on stock_prices.
These were missing before Sprint 6; queries that filter by ticker (almost every
API endpoint) now use the index instead of a full table scan.
