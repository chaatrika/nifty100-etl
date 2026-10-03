# run_ratio_engine.py
# Runs all the ratio formulas for every company and year and fills the
# financial_ratios table (Sprint 2, Day 12 and 13).
#
# Run from the project root:   python3 -m src.analytics.run_ratio_engine   (or: make ratios)
#
# Reads  : data/nifty100.db  (profitandloss, balancesheet, cashflow, companies, sectors)
# Writes : financial_ratios table (dropped and created again with the extra columns)
#          output/capital_allocation.csv
#          output/ratio_edge_cases.log

import logging
import os
import sqlite3

import pandas as pd

from . import ratios as R
from . import cagr as C
from . import cashflow_kpis as K

DB_PATH = os.path.join("data", "nifty100.db")
OUT_DIR = "output"

DDL = """
DROP TABLE IF EXISTS financial_ratios;
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
CREATE INDEX idx_fr_company ON financial_ratios(company_id);
"""



class LogCollector(logging.Handler):
    # small helper so we can keep the OPM warnings in a list and write them
    # to the log file at the end
    def __init__(self):
        logging.Handler.__init__(self)
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def not_null(row, col):
    # get a value from a row, or None if it is empty
    value = row.get(col)
    if value is None or pd.isna(value):
        return None
    return value


def composite_score(de, roe, cfo_quality, revenue_cagr):
    # simple score out of 100. Each of the 4 parts gives up to 25 points.
    # If a part is missing we skip it and scale the rest to 100.
    points = []

    if roe is not None:
        if roe >= 15:
            points.append(25)
        elif roe >= 8:
            points.append(12.5)
        else:
            points.append(0)

    if de is not None:
        if de < 1:
            points.append(25)
        elif de < 2:
            points.append(12.5)
        else:
            points.append(0)

    if cfo_quality is not None:
        if cfo_quality >= 1.0:
            points.append(25)
        elif cfo_quality >= 0.5:
            points.append(12.5)
        else:
            points.append(0)

    if revenue_cagr is not None:
        if revenue_cagr >= 10:
            points.append(25)
        elif revenue_cagr >= 5:
            points.append(12.5)
        else:
            points.append(0)

    if len(points) == 0:
        return None
    return round(sum(points) * 4 / len(points), 1)


def load_data(conn):
    # read the tables and join them into one big table (one row per company + year)
    pl = pd.read_sql("SELECT * FROM profitandloss", conn).drop(columns=["row_id"])
    bs = pd.read_sql("SELECT * FROM balancesheet", conn).drop(columns=["row_id"])
    cf = pd.read_sql("SELECT * FROM cashflow", conn).drop(columns=["row_id"])
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id AS company_id, face_value FROM companies", conn)

    keys = ["company_id", "year"]
    df = pl.merge(bs, on=keys, how="outer")
    df = df.merge(cf, on=keys, how="outer")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(companies, on="company_id", how="left")
    df = df.sort_values(keys).reset_index(drop=True)

    # year looks like "2024-03", we keep just the 4 digit year for CAGR
    df["fy"] = df["year"].str[:4].astype(int)
    return df


def build_ratios(df):
    # EBIT = profit before tax + interest
    df["ebit"] = df["profit_before_tax"] + df["interest"].fillna(0)

    # ROCE for every row first, so we can get the sector median for banks
    roce_list = []
    for i in range(len(df)):
        row = df.iloc[i]
        roce_list.append(R.return_on_capital_employed(row["ebit"], row["equity_capital"],
                                                      row["reserves"], row["borrowings"]))
    df["roce"] = roce_list
    sector_median = df.groupby(["broad_sector", "fy"])["roce"].median().to_dict()

    results = []

    for company_id, group in df.groupby("company_id"):
        group = group.reset_index(drop=True)

        # yearly series for the CAGR. Empty values are skipped so a stub row
        # like 2024-09 (balance sheet only) can't wipe out the real 2024-03 value.
        series = {}
        for name, col in [("revenue", "sales"), ("pat", "net_profit"), ("eps", "eps")]:
            d = {}
            for fy, value in zip(group["fy"], group[col]):
                if pd.notna(value):
                    d[fy] = value
            series[name] = d

        for i in range(len(group)):
            r = group.iloc[i].to_dict()
            sector = not_null(r, "broad_sector")

            sales = not_null(r, "sales")
            net_profit = not_null(r, "net_profit")
            equity = not_null(r, "equity_capital")
            reserves = not_null(r, "reserves")
            borrowings = not_null(r, "borrowings")
            cfo = not_null(r, "operating_activity")
            cfi = not_null(r, "investing_activity")

            opm = R.operating_profit_margin(not_null(r, "operating_profit"), sales)
            R.opm_mismatch(opm, not_null(r, "opm_percentage"), company_id=company_id, year=r["year"])

            de = R.debt_to_equity(borrowings, equity, reserves)
            icr = R.interest_coverage(not_null(r, "operating_profit"), not_null(r, "other_income"),
                                      not_null(r, "interest"))
            roe = R.return_on_equity(net_profit, equity, reserves)
            roce = not_null(r, "roce")
            fcf = K.free_cash_flow(cfo, cfi)
            capex_pct = K.capex_intensity(cfi, sales)

            # cash flow quality uses the last 5 rows of this company
            last5 = group.iloc[max(0, i - 4): i + 1]
            cfo_quality = K.cfo_quality_score(list(last5["operating_activity"]), list(last5["net_profit"]))

            # book value per share = (equity + reserves) / number of shares
            # number of shares = equity capital / face value
            book_value = None
            face_value = not_null(r, "face_value")
            if face_value and equity and equity > 0 and face_value > 0:
                shares = equity / face_value
                book_value = (equity + (reserves or 0)) / shares

            row = {}
            row["company_id"] = company_id
            row["year"] = r["year"]
            row["net_profit_margin_pct"] = R.net_profit_margin(net_profit, sales)
            row["operating_profit_margin_pct"] = opm
            row["return_on_equity_pct"] = roe
            row["debt_to_equity"] = de
            row["interest_coverage"] = icr
            row["asset_turnover"] = R.asset_turnover(sales, not_null(r, "total_assets"))
            row["free_cash_flow_cr"] = fcf
            row["capex_cr"] = abs(cfi) if cfi is not None else None
            row["earnings_per_share"] = not_null(r, "eps")
            row["book_value_per_share"] = book_value
            row["dividend_payout_ratio_pct"] = not_null(r, "dividend_payout")
            row["total_debt_cr"] = borrowings
            row["cash_from_operations_cr"] = cfo
            row["return_on_capital_employed_pct"] = roce

            # banks are compared with their sector median
            row["roce_vs_sector"] = None
            if sector == R.FINANCIAL_SECTOR:
                median = sector_median.get((sector, r["fy"]))
                row["roce_vs_sector"] = R.roce_vs_sector(roce, median)

            row["return_on_assets_pct"] = R.return_on_assets(net_profit, not_null(r, "total_assets"))
            row["high_leverage_flag"] = int(R.high_leverage_flag(de, sector))
            row["icr_label"] = R.icr_label(icr, not_null(r, "interest"))
            row["icr_warning_flag"] = int(R.icr_warning_flag(icr))
            row["net_debt_cr"] = R.net_debt(borrowings, not_null(r, "investments"))
            row["capex_intensity_pct"] = capex_pct
            row["capex_label"] = K.capex_label(capex_pct)
            row["fcf_conversion_pct"] = K.fcf_conversion(fcf, not_null(r, "operating_profit"))
            row["cfo_quality_score"] = cfo_quality
            row["cfo_quality_label"] = K.cfo_quality_label(cfo_quality)

            # growth rates (3, 5 and 10 years) ending in this row's year
            for name in ["revenue", "pat", "eps"]:
                row.update(C.all_cagrs(series[name], name, end_year=r["fy"]))

            row["composite_quality_score"] = composite_score(de, roe, cfo_quality, row["revenue_cagr_5yr"])
            results.append(row)

    out = pd.DataFrame(results)
    out.insert(0, "row_id", range(1, len(out) + 1))
    return out


def suggest_category(computed, src_value, sector):
    # a first guess for the category. A person still has to check each line.
    if abs(src_value) < 1 or abs(src_value) > 100:
        return "data source issue", "source value looks like a ratio or an outlier, not a percentage"
    if abs(computed) > 100:
        return "data source issue", "our value is impossible (over 100%), so equity/reserves in the data look wrong"
    if sector == R.FINANCIAL_SECTOR:
        return "formula discrepancy", "bank / NBFC capital base is different from the normal formula"
    return "version difference", "source is a latest/TTM figure, ours is the latest annual year"


def write_edge_case_log(conn, ratios_df, opm_lines, path, limit=5.0):
    # compare our ROE and ROCE with the ready-made values in the companies table
    companies = pd.read_sql("SELECT id AS company_id, roe_percentage, roce_percentage FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)

    # use the latest year that really has profit data
    with_data = ratios_df[ratios_df["net_profit_margin_pct"].notna()]
    latest = with_data.sort_values("year").groupby("company_id").tail(1)
    latest = latest.merge(companies, on="company_id").merge(sectors, on="company_id", how="left")

    count = 0
    f = open(path, "w")
    f.write("# ratio_edge_cases.log (category is a first guess - confirm every line in the Day 14 review)\n")
    f.write("# company | metric | computed | source | diff | category | reason\n")

    for i in range(len(latest)):
        r = latest.iloc[i]
        pairs = [("ROE", r["return_on_equity_pct"], r["roe_percentage"]),
                 ("ROCE", r["return_on_capital_employed_pct"], r["roce_percentage"])]
        for metric, computed, source in pairs:
            if pd.isna(computed) or pd.isna(source):
                continue
            diff = abs(computed - float(source))
            if diff > limit:
                category, reason = suggest_category(computed, float(source), r["broad_sector"])
                f.write("%s | %s | %.2f | %.2f | %.2f | %s | %s\n" % (
                    r["company_id"], metric, computed, float(source), diff, category, reason))
                count += 1

    f.write("\n# OPM difference bigger than 1 point: %d rows\n" % len(opm_lines))
    for line in opm_lines:
        f.write(line + "\n")
    f.close()
    return count


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # collect the OPM warnings from ratios.py
    collector = LogCollector()
    R.log.addHandler(collector)
    R.log.setLevel(logging.WARNING)
    R.log.propagate = False

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    df = load_data(conn)
    ratios_df = build_ratios(df)

    # rebuild the table and save
    conn.executescript(DDL)
    ratios_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()

    # capital allocation csv
    cf = pd.read_sql(
        "SELECT c.company_id, c.year, c.operating_activity AS cfo, c.investing_activity AS cfi, "
        "c.financing_activity AS cff, p.net_profit "
        "FROM cashflow c LEFT JOIN profitandloss p ON p.company_id = c.company_id AND p.year = c.year", conn)
    cf["cfo_pat_ratio"] = cf["cfo"] / cf["net_profit"].where(cf["net_profit"] != 0)
    K.write_capital_allocation_csv(cf.to_dict("records"), os.path.join(OUT_DIR, "capital_allocation.csv"))

    gaps = write_edge_case_log(conn, ratios_df, collector.lines, os.path.join(OUT_DIR, "ratio_edge_cases.log"))

    print("financial_ratios rows  :", len(ratios_df))
    print("capital_allocation rows:", len(cf))
    print("edge case log          :", gaps, "ROE/ROCE gaps,", len(collector.lines), "OPM gaps")


if __name__ == "__main__":
    main()
