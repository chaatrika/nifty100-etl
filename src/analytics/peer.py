# peer.py
# Percentile ranking of every company against the others in its peer group
# (Sprint 3, Day 18). Fills the peer_percentiles table.
#
# Run from the project root:   python -m src.analytics.peer

import os
import sqlite3

import numpy as np
import pandas as pd

DB_PATH = os.path.join("data", "nifty100.db")
NO_GROUP_MESSAGE = "No peer group assigned"

# (column in financial_ratios, True if lower is better)
METRICS = [
    ("return_on_equity_pct", False),
    ("return_on_capital_employed_pct", False),
    ("net_profit_margin_pct", False),
    ("debt_to_equity", True),          # lower D/E is better, so the percentile is flipped
    ("free_cash_flow_cr", False),
    ("pat_cagr_5yr", False),
    ("revenue_cagr_5yr", False),
    ("eps_cagr_5yr", False),
    ("interest_coverage", False),
    ("asset_turnover", False),
]

DDL = """
DROP TABLE IF EXISTS peer_percentiles;
CREATE TABLE peer_percentiles (
    company_id       TEXT NOT NULL,
    peer_group_name  TEXT NOT NULL,
    metric           TEXT NOT NULL,
    value            NUMERIC,
    percentile_rank  NUMERIC,
    year             INTEGER NOT NULL,
    PRIMARY KEY (company_id, peer_group_name, metric, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE INDEX idx_pp_company ON peer_percentiles(company_id);
"""


def percent_rank(values):
    # same as SQL PERCENT_RANK: (rank - 1) / (n - 1), where rank 1 = smallest value.
    # Empty values are left out. With fewer than 2 values there is nothing to rank.
    values = pd.Series(values, dtype="float64")
    result = pd.Series(np.nan, index=values.index)
    valid = values.notna()
    n = valid.sum()
    if n < 2:
        return result
    ranks = values[valid].rank(method="min")
    result[valid] = (ranks - 1) / (n - 1)
    return result


def load_yearly_ratios(conn):
    # one row per company and fiscal year (only rows that have profit data)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr = fr[fr["net_profit_margin_pct"].notna()].copy()
    fr["fy"] = fr["year"].str[:4].astype(int)
    fr = fr.sort_values(["company_id", "year"])
    fr = fr.drop_duplicates(["company_id", "fy"], keep="last")
    return fr


def compute_peer_percentiles(conn):
    fr = load_yearly_ratios(conn)
    groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)

    rows = []
    for group_name, members in groups.groupby("peer_group_name"):
        data = fr[fr["company_id"].isin(members["company_id"])]

        for fy, year_data in data.groupby("fy"):
            year_data = year_data.set_index("company_id")

            for column, lower_is_better in METRICS:
                values = year_data[column].copy()

                # debt free companies have no interest, so coverage is empty.
                # For ranking we treat them as the best possible (infinity).
                is_debt_free = pd.Series(False, index=year_data.index)
                if column == "interest_coverage":
                    is_debt_free = year_data["icr_label"] == "Debt Free"
                    values[is_debt_free] = np.inf

                pr = percent_rank(values)
                if lower_is_better:
                    pr = 1 - pr

                for company_id in year_data.index:
                    if pd.isna(pr[company_id]):
                        continue
                    shown_value = None if is_debt_free[company_id] else float(values[company_id])
                    rows.append({
                        "company_id": company_id,
                        "peer_group_name": group_name,
                        "metric": column,
                        "value": shown_value,
                        "percentile_rank": round(float(pr[company_id]), 4),
                        "year": int(fy),
                    })
    return pd.DataFrame(rows)


def save_peer_percentiles(conn, df):
    conn.executescript(DDL)
    df.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()


def get_peer_group(conn, company_id):
    row = conn.execute("SELECT peer_group_name FROM peer_groups WHERE company_id = ?",
                       (company_id,)).fetchone()
    if row is None:
        return None
    return row[0]


def get_company_percentiles(conn, company_id):
    # latest percentiles for one company.
    # If the company is not in any peer group we return a message, not an error.
    group = get_peer_group(conn, company_id)
    if group is None:
        return NO_GROUP_MESSAGE
    df = pd.read_sql("SELECT * FROM peer_percentiles WHERE company_id = ?", conn, params=(company_id,))
    if len(df) == 0:
        return NO_GROUP_MESSAGE
    return df[df["year"] == df["year"].max()].reset_index(drop=True)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    df = compute_peer_percentiles(conn)
    save_peer_percentiles(conn, df)
    groups = df["peer_group_name"].nunique()
    print("peer_percentiles rows:", len(df), "| peer groups:", groups, "| metrics:", df["metric"].nunique())
    conn.close()


if __name__ == "__main__":
    main()
