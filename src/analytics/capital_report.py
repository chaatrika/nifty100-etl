# capital_report.py - checks and summaries for output/capital_allocation.csv (Sprint 5, Day 32)
#
# Run from the project root:   python -m src.analytics.capital_report
# Writes : output/capital_allocation_gaps.csv   companies/years that have cash flow data but no pattern
#          output/pattern_distribution.csv      companies per pattern in the latest year (all 8 patterns)
#          output/pattern_changes.csv           companies that moved from one pattern to another

import os

import pandas as pd

from src.analytics import series

OUT_DIR = "output"
PATTERNS = ["Shareholder Returns", "Reinvestor", "Growth Funded by Debt", "Liquidating Assets",
            "Mixed", "Distress Signal", "Cash Accumulator", "Pre-Revenue"]


def load_patterns(path=os.path.join(OUT_DIR, "capital_allocation.csv")):
    return series.annual(pd.read_csv(path), "pattern_label")


def find_gaps(pat, cf, companies):
    have = set(zip(pat["company_id"], pat["fy"]))
    rows = [(r.company_id, int(r.fy)) for r in cf.itertuples() if (r.company_id, int(r.fy)) not in have]
    gaps = pd.DataFrame(rows, columns=["company_id", "fy"])
    no_rows = sorted(set(companies) - set(pat["company_id"]))
    return gaps, no_rows


def distribution(pat):
    latest_fy = int(pat["fy"].max())
    counts = pat[pat["fy"] == latest_fy]["pattern_label"].value_counts()
    return latest_fy, pd.DataFrame({"pattern": PATTERNS, "companies": [int(counts.get(p, 0)) for p in PATTERNS]})


def changes(pat):
    rows = []
    for cid, g in pat.sort_values("fy").groupby("company_id"):
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            if g.loc[i, "pattern_label"] != g.loc[i - 1, "pattern_label"]:
                rows.append((cid, int(g.loc[i - 1, "fy"]), int(g.loc[i, "fy"]),
                             g.loc[i - 1, "pattern_label"], g.loc[i, "pattern_label"]))
    return pd.DataFrame(rows, columns=["company_id", "from_year", "to_year", "from_pattern", "to_pattern"])


def main():
    data = series.load_all()
    pat = load_patterns()
    gaps, missing = find_gaps(pat, data["cf"], data["companies"]["company_id"])
    latest_fy, dist = distribution(pat)
    chg = changes(pat)
    gap_out = pd.concat([gaps, pd.DataFrame({"company_id": missing, "fy": "no rows at all"})], ignore_index=True)
    gap_out.to_csv(os.path.join(OUT_DIR, "capital_allocation_gaps.csv"), index=False)
    dist.to_csv(os.path.join(OUT_DIR, "pattern_distribution.csv"), index=False)
    chg.to_csv(os.path.join(OUT_DIR, "pattern_changes.csv"), index=False)
    print(f"Completeness: {pat['company_id'].nunique()} of {len(data['companies'])} companies have a pattern")
    print(f"  companies with no pattern rows: {missing or 'none'}")
    print(f"  company-years with cash flow data but no pattern: {len(gaps)}")
    print(f"Distribution for {latest_fy}:\n{dist.to_string(index=False)}")
    print(f"Pattern changes: {len(chg)} (see output/pattern_changes.csv)")


if __name__ == "__main__":
    main()
