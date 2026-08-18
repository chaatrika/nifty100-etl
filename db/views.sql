-- ===================================================
-- Nifty 100 Financial Database - Analytical Views
-- ===================================================

-- 1. View: Financial Ratios Summary
-- Calculates Net Profit Margin, ROE, and Debt-to-Equity
CREATE VIEW IF NOT EXISTS v_financial_ratios AS
SELECT 
    c.company_id,
    c.ticker,
    c.company_name,
    p.year,
    p.sales,
    p.net_profit,
    b.equity_capital + b.reserves AS total_equity,
    b.borrowings AS total_debt,
    ROUND((p.net_profit / NULLIF(p.sales, 0)) * 100, 2) AS net_profit_margin_pct,
    ROUND((p.net_profit / NULLIF((b.equity_capital + b.reserves), 0)) * 100, 2) AS roe_pct,
    ROUND(b.borrowings / NULLIF((b.equity_capital + b.reserves), 0), 2) AS debt_to_equity
FROM companies c
JOIN profitandloss p ON c.company_id = p.company_id
JOIN balancesheet b ON c.company_id = b.company_id AND p.year = b.year;

-- 2. View: Cash Flow Analysis
-- Summarizes operating vs investing cash flow dynamics
CREATE VIEW IF NOT EXISTS v_cashflow_summary AS
SELECT 
    c.ticker,
    c.company_name,
    cf.year,
    cf.operating_cash_flow,
    cf.investing_cash_flow,
    cf.financing_cash_flow,
    (cf.operating_cash_flow + cf.investing_cash_flow) AS free_cash_flow
FROM companies c
JOIN cashflow cf ON c.company_id = cf.company_id;