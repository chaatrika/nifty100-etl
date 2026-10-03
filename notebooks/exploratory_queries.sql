-- Sprint 1, Day 07 — Exploratory queries: row counts, nulls, year coverage per company
-- Run against data/nifty100.db

-- 1. Row counts across all 10 core/supplementary tables loaded
SELECT 'companies' AS tbl, COUNT(*) AS rows FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- 2. Companies with fewer than 5 years of P&L history (coverage check, DQ-16)
SELECT company_id, COUNT(DISTINCT year) AS pl_years
FROM profitandloss
GROUP BY company_id
HAVING pl_years < 5
ORDER BY pl_years;

-- 3. Null counts for key P&L fields
SELECT
  SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
  SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_net_profit,
  SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps,
  SUM(CASE WHEN interest IS NULL THEN 1 ELSE 0 END) AS null_interest
FROM profitandloss;

-- 4. Year distribution (earliest / latest year per company) for balance sheet
SELECT company_id, MIN(year) AS earliest_year, MAX(year) AS latest_year, COUNT(*) AS n_years
FROM balancesheet
GROUP BY company_id
ORDER BY n_years ASC
LIMIT 15;

-- 5. Companies missing from sectors table (should be zero — sectors has 100% coverage)
SELECT c.id, c.company_name
FROM companies c
LEFT JOIN sectors s ON c.id = s.company_id
WHERE s.company_id IS NULL;

-- 6. Companies with zero annual report links (documents coverage gap)
SELECT c.id, c.company_name
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id
GROUP BY c.id
HAVING COUNT(d.row_id) = 0;

-- 7. Balance sheet rows where assets != liabilities by more than 1% (DQ-04 spot check)
SELECT company_id, year, total_assets, total_liabilities,
       ROUND(ABS(total_assets - total_liabilities) * 100.0 / NULLIF(total_assets, 0), 2) AS pct_diff
FROM balancesheet
WHERE total_assets IS NOT NULL AND total_liabilities IS NOT NULL AND total_assets != 0
  AND ABS(total_assets - total_liabilities) * 1.0 / total_assets >= 0.01
ORDER BY pct_diff DESC
LIMIT 20;

-- 8. Debt-free companies (borrowings = 0) in latest balance sheet year
SELECT company_id, year, borrowings
FROM balancesheet
WHERE borrowings = 0
ORDER BY year DESC;

-- 9. Sector distribution — company count per broad_sector
SELECT broad_sector, COUNT(*) AS n_companies
FROM sectors
GROUP BY broad_sector
ORDER BY n_companies DESC;

-- 10. Peer group membership counts
SELECT peer_group_name, COUNT(*) AS n_members,
       SUM(CASE WHEN is_benchmark = 1 THEN 1 ELSE 0 END) AS n_benchmarks
FROM peer_groups
GROUP BY peer_group_name
ORDER BY n_members DESC;
