-- Nifty 100 Financial Intelligence Platform — SQLite schema (10 tables)
-- Sprint 1, Day 04

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS market_cap;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS peer_percentiles;

CREATE TABLE companies (
    id                  TEXT PRIMARY KEY,
    company_logo        TEXT,
    company_name        TEXT NOT NULL,
    chart_link          TEXT,
    about_company       TEXT,
    website             TEXT,
    nse_profile         TEXT,
    bse_profile         TEXT,
    face_value          NUMERIC,
    book_value          NUMERIC,
    roce_percentage     NUMERIC,
    roe_percentage      NUMERIC
);

CREATE TABLE profitandloss (
    row_id              INTEGER,
    company_id          TEXT NOT NULL,
    year                TEXT NOT NULL,
    sales               NUMERIC,
    expenses            NUMERIC,
    operating_profit    NUMERIC,
    opm_percentage      NUMERIC,
    other_income        NUMERIC,
    interest            NUMERIC,
    depreciation        NUMERIC,
    profit_before_tax   NUMERIC,
    tax_percentage      NUMERIC,
    net_profit          NUMERIC,
    eps                 NUMERIC,
    dividend_payout     NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE balancesheet (
    row_id              INTEGER,
    company_id          TEXT NOT NULL,
    year                TEXT NOT NULL,
    equity_capital      NUMERIC,
    reserves            NUMERIC,
    borrowings          NUMERIC,
    other_liabilities   NUMERIC,
    total_liabilities   NUMERIC,
    fixed_assets        NUMERIC,
    cwip                NUMERIC,
    investments         NUMERIC,
    other_asset         NUMERIC,
    total_assets        NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE cashflow (
    row_id              INTEGER,
    company_id          TEXT NOT NULL,
    year                TEXT NOT NULL,
    operating_activity  NUMERIC,
    investing_activity  NUMERIC,
    financing_activity  NUMERIC,
    net_cash_flow       NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE analysis (
    row_id                      INTEGER,
    company_id                  TEXT NOT NULL,
    compounded_sales_growth     TEXT,
    compounded_profit_growth    TEXT,
    stock_price_cagr            TEXT,
    roe                         TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE documents (
    row_id          INTEGER,
    company_id      TEXT NOT NULL,
    year            INTEGER NOT NULL,
    annual_report   TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE prosandcons (
    row_id          INTEGER,
    company_id      TEXT NOT NULL,
    pros            TEXT,
    cons            TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE sectors (
    row_id                  INTEGER,
    company_id              TEXT PRIMARY KEY,
    broad_sector            TEXT,
    sub_sector              TEXT,
    index_weight_pct        NUMERIC,
    market_cap_category     TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE stock_prices (
    row_id          INTEGER,
    company_id      TEXT NOT NULL,
    date            TEXT NOT NULL,
    open_price      NUMERIC,
    high_price      NUMERIC,
    low_price       NUMERIC,
    close_price     NUMERIC,
    volume          INTEGER,
    adjusted_close  NUMERIC,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE market_cap (
    row_id                  INTEGER,
    company_id              TEXT NOT NULL,
    year                    INTEGER NOT NULL,
    market_cap_crore        NUMERIC,
    enterprise_value_crore  NUMERIC,
    pe_ratio                NUMERIC,
    pb_ratio                NUMERIC,
    ev_ebitda               NUMERIC,
    dividend_yield_pct      NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE financial_ratios (
    row_id                          INTEGER,
    company_id                      TEXT NOT NULL,
    year                            TEXT NOT NULL,
    net_profit_margin_pct           NUMERIC,
    operating_profit_margin_pct     NUMERIC,
    return_on_equity_pct            NUMERIC,
    debt_to_equity                  NUMERIC,
    interest_coverage               NUMERIC,
    asset_turnover                  NUMERIC,
    free_cash_flow_cr               NUMERIC,
    capex_cr                        NUMERIC,
    earnings_per_share              NUMERIC,
    book_value_per_share            NUMERIC,
    dividend_payout_ratio_pct       NUMERIC,
    total_debt_cr                   NUMERIC,
    cash_from_operations_cr         NUMERIC,
    return_on_capital_employed_pct  NUMERIC,
    roce_vs_sector                  TEXT,
    return_on_assets_pct            NUMERIC,
    high_leverage_flag              INTEGER,
    icr_label                       TEXT,
    icr_warning_flag                INTEGER,
    net_debt_cr                     NUMERIC,
    capex_intensity_pct             NUMERIC,
    capex_label                     TEXT,
    fcf_conversion_pct              NUMERIC,
    cfo_quality_score               NUMERIC,
    cfo_quality_label               TEXT,
    revenue_cagr_3yr NUMERIC, revenue_cagr_3yr_flag TEXT,
    revenue_cagr_5yr NUMERIC, revenue_cagr_5yr_flag TEXT,
    revenue_cagr_10yr NUMERIC, revenue_cagr_10yr_flag TEXT,
    pat_cagr_3yr NUMERIC, pat_cagr_3yr_flag TEXT,
    pat_cagr_5yr NUMERIC, pat_cagr_5yr_flag TEXT,
    pat_cagr_10yr NUMERIC, pat_cagr_10yr_flag TEXT,
    eps_cagr_3yr NUMERIC, eps_cagr_3yr_flag TEXT,
    eps_cagr_5yr NUMERIC, eps_cagr_5yr_flag TEXT,
    eps_cagr_10yr NUMERIC, eps_cagr_10yr_flag TEXT,
    composite_quality_score         NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE peer_groups (
    row_id              INTEGER,
    peer_group_name     TEXT NOT NULL,
    company_id          TEXT NOT NULL,
    is_benchmark        INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE peer_percentiles (
    company_id          TEXT NOT NULL,
    peer_group_name     TEXT NOT NULL,
    metric              TEXT NOT NULL,
    value               NUMERIC,
    percentile_rank     NUMERIC,
    year                INTEGER NOT NULL,
    PRIMARY KEY (company_id, peer_group_name, metric, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_pl_company ON profitandloss(company_id);
CREATE INDEX idx_bs_company ON balancesheet(company_id);
CREATE INDEX idx_cf_company ON cashflow(company_id);
CREATE INDEX idx_docs_company ON documents(company_id);
CREATE INDEX idx_sp_company ON stock_prices(company_id);
CREATE INDEX idx_mc_company ON market_cap(company_id);
CREATE INDEX idx_fr_company ON financial_ratios(company_id);
CREATE INDEX idx_pg_company ON peer_groups(company_id);
CREATE INDEX idx_pp_company ON peer_percentiles(company_id);
