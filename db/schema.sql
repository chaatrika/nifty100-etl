PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sectors (
    sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    sector_id INTEGER,
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
);

CREATE TABLE IF NOT EXISTS profitandloss (
    company_id INTEGER,
    year INTEGER,
    sales REAL,
    expenses REAL,
    opm REAL,
    net_profit REAL,
    eps REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS balancesheet (
    company_id INTEGER,
    year INTEGER,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    other_assets REAL,
    total_assets REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS cashflow (
    company_id INTEGER,
    year INTEGER,
    operating_cash_flow REAL,
    investing_cash_flow REAL,
    financing_cash_flow REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id INTEGER,
    date TEXT,
    close_price REAL,
    volume INTEGER,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id INTEGER,
    year INTEGER,
    roce REAL,
    roe REAL,
    debt_to_equity REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS peer_groups (
    company_id INTEGER,
    peer_company_id INTEGER,
    PRIMARY KEY (company_id, peer_company_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (peer_company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS analysis (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    year INTEGER,
    notes TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    year INTEGER,
    doc_type TEXT,
    doc_url TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    type TEXT CHECK(type IN ('PRO', 'CON')),
    description TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);