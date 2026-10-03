# parser.py - turns the text in analysis.xlsx ("10 Years: 21%") into numbers (Sprint 5, Day 29)
#
# Run from the project root:   python -m src.nlp.parser
#
# Reads  : data/raw/analysis.xlsx, data/nifty100.db (to check company ids and cross-check CAGR)
# Writes : output/analysis_parsed.csv      company_id, metric_type, period_years, value_pct
#          output/parse_failures.csv       text that did not match (or company not in our 92)
#          output/analysis_crosscheck.csv  parsed CAGR vs computed CAGR, flag if they differ by more than 5 points

import os
import re
import sqlite3

import pandas as pd

from src.analytics import series

RAW_FILE = os.path.join("data", "raw", "analysis.xlsx")
OUT_DIR = "output"
FIELDS = ["compounded_sales_growth", "compounded_profit_growth", "stock_price_cagr", "roe"]
# the pattern from the plan, plus an optional minus sign so "1 Year: -2%" is not lost
PATTERN = re.compile(r"(\d+)\s*Years?:?\s*(-?[\d.]+)%", re.IGNORECASE)
# analysis field -> column prefix in financial_ratios
CAGR_COLUMN = {"compounded_sales_growth": "revenue_cagr_{}yr", "compounded_profit_growth": "pat_cagr_{}yr"}
DIVERGENCE_PP = 5.0


def parse_text(text):
    # returns (period_years, value_pct) or None
    m = PATTERN.search(str(text))
    if not m:
        return None
    return int(m.group(1)), float(m.group(2))


def read_raw(path=RAW_FILE):
    df = pd.read_excel(path, header=1)          # row 0 is a title line
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_frame(df, valid_ids):
    parsed, failures = [], []
    for row in df.itertuples(index=False):
        rec = row._asdict()
        cid = rec["company_id"]
        for field in FIELDS:
            text = rec.get(field)
            if cid not in valid_ids:
                failures.append((cid, field, text, "company not in companies table"))
                continue
            hit = parse_text(text)
            if hit is None:
                failures.append((cid, field, text, "text does not match 'N Years: X%'"))
            else:
                parsed.append((cid, field, hit[0], hit[1]))
    parsed = pd.DataFrame(parsed, columns=["company_id", "metric_type", "period_years", "value_pct"])
    failures = pd.DataFrame(failures, columns=["company_id", "metric_type", "raw_text", "reason"])
    return parsed.drop_duplicates(), failures


def cross_check(parsed, ratios_latest):
    rows = []
    latest = ratios_latest.set_index("company_id")
    for r in parsed.itertuples():
        pattern = CAGR_COLUMN.get(r.metric_type)
        if pattern is None or r.period_years not in (3, 5, 10) or r.company_id not in latest.index:
            continue
        computed = latest.loc[r.company_id].get(pattern.format(r.period_years))
        diff = None if pd.isna(computed) else r.value_pct - computed
        flag = "no computed value" if diff is None else ("REVIEW" if abs(diff) > DIVERGENCE_PP else "ok")
        rows.append((r.company_id, r.metric_type, r.period_years, r.value_pct,
                     None if pd.isna(computed) else round(float(computed), 2),
                     None if diff is None else round(float(diff), 2), flag))
    return pd.DataFrame(rows, columns=["company_id", "metric_type", "period_years", "parsed_pct",
                                       "computed_pct", "diff_points", "flag"])


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    data = series.load_all()
    valid = set(data["companies"]["company_id"])
    parsed, failures = parse_frame(read_raw(), valid)
    latest = data["ratios"].sort_values("fy").groupby("company_id").tail(1)
    check = cross_check(parsed, latest)

    parsed.to_csv(os.path.join(OUT_DIR, "analysis_parsed.csv"), index=False)
    failures.to_csv(os.path.join(OUT_DIR, "parse_failures.csv"), index=False)
    check.to_csv(os.path.join(OUT_DIR, "analysis_crosscheck.csv"), index=False)
    print(f"Parsed {len(parsed)} values for {parsed['company_id'].nunique()} companies")
    print(f"Not parsed: {len(failures)} (see output/parse_failures.csv)")
    print(f"Cross-check: {len(check)} compared, {(check['flag'] == 'REVIEW').sum()} need manual review")


if __name__ == "__main__":
    main()
