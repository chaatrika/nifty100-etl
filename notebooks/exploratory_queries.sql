-- ===================================================
-- Nifty 100 Financial Database - Exploratory Queries
-- ===================================================

-- 1. Check loaded company count and list distinct tickers
SELECT 
    COUNT(*) AS total_companies,
    GROUP_CONCAT(ticker, ', ') AS loaded_tickers
FROM companies;

-- 2. Inspect Audit Log Execution History
-- Run via SQLite CLI or pandas read_sql
SELECT * FROM load_audit ORDER BY rowid DESC;

-- 3. Verify Foreign Key integrity between Companies and Balance Sheet
SELECT 
    c.company_id,
    c.ticker,
    c.company_name,
    COUNT(b.year) AS balance_sheet_years
FROM companies c
LEFT JOIN balancesheet b ON c.company_id = b.company_id
GROUP BY c.company_id, c.ticker, c.company_name;

-- 4. Audit Data Quality: Check for orphaned financial records
SELECT 'ProfitAndLoss' AS table_name, COUNT(*) AS orphaned_records 
FROM profitandloss WHERE company_id NOT IN (SELECT company_id FROM companies)
UNION ALL
SELECT 'BalanceSheet' AS table_name, COUNT(*) AS orphaned_records 
FROM balancesheet WHERE company_id NOT IN (SELECT company_id FROM companies)
UNION ALL
SELECT 'CashFlow' AS table_name, COUNT(*) AS orphaned_records 
FROM cashflow WHERE company_id NOT IN (SELECT company_id FROM companies);