# cashflow_kpis.py
# Cash flow measures and the capital allocation pattern - Sprint 2, Day 11.

import csv
import math


def to_num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(x):
        return None
    return x


def free_cash_flow(operating_activity, investing_activity):
    # operating cash flow + investing cash flow (a negative answer is fine)
    cfo = to_num(operating_activity)
    cfi = to_num(investing_activity)
    if cfo is None or cfi is None:
        return None
    return cfo + cfi


def cfo_quality_score(cfo_list, pat_list, years=5):
    # average of (cash from operations / net profit) over the last 5 years
    # years where profit is 0 are skipped
    ratios = []
    pairs = list(zip(cfo_list, pat_list))
    for cfo, pat in pairs[-years:]:
        cfo = to_num(cfo)
        pat = to_num(pat)
        if cfo is None or pat is None or pat == 0:
            continue
        ratios.append(cfo / pat)
    if len(ratios) == 0:
        return None
    return sum(ratios) / len(ratios)


def cfo_quality_label(score):
    score = to_num(score)
    if score is None:
        return None
    if score > 1.0:
        return "High Quality"
    if score >= 0.5:
        return "Moderate"
    return "Accrual Risk"


def capex_intensity(investing_activity, sales):
    # abs(investing cash flow) / sales x 100
    cfi = to_num(investing_activity)
    s = to_num(sales)
    if cfi is None or s is None or s == 0:
        return None
    return abs(cfi) / s * 100


def capex_label(intensity):
    intensity = to_num(intensity)
    if intensity is None:
        return None
    if intensity < 3:
        return "Asset Light"
    if intensity <= 8:
        return "Moderate"
    return "Capital Intensive"


def fcf_conversion(fcf, operating_profit):
    # free cash flow / operating profit x 100
    f = to_num(fcf)
    op = to_num(operating_profit)
    if f is None or op is None or op == 0:
        return None
    return f / op * 100


def sign(x):
    # "+" for zero or more, "-" for negative
    x = to_num(x)
    if x is None:
        return None
    if x >= 0:
        return "+"
    return "-"


def classify_pattern(cfo, cfi, cff, cfo_pat_ratio=None, high_ratio=1.0):
    # look at the sign of operating, investing and financing cash flow
    s = (sign(cfo), sign(cfi), sign(cff))
    if None in s:
        return None

    if s == ("+", "-", "-"):
        # same signs, so we use CFO / profit to split them into two labels
        ratio = to_num(cfo_pat_ratio)
        if ratio is not None and ratio > high_ratio:
            return "Shareholder Returns"
        return "Reinvestor"
    if s == ("+", "+", "-"):
        return "Liquidating Assets"
    if s == ("-", "+", "+"):
        return "Distress Signal"
    if s == ("-", "-", "+"):
        return "Growth Funded by Debt"
    if s == ("+", "+", "+"):
        return "Cash Accumulator"
    if s == ("-", "-", "-"):
        return "Pre-Revenue"
    # (+,-,+) is Mixed. (-,+,-) is not in the spec so it also goes to Mixed
    return "Mixed"


def write_capital_allocation_csv(rows, path="output/capital_allocation.csv"):
    # rows = list of dicts with company_id, year, cfo, cfi, cff and cfo_pat_ratio
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"])
        for r in rows:
            label = classify_pattern(r["cfo"], r["cfi"], r["cff"], r.get("cfo_pat_ratio"))
            writer.writerow([r["company_id"], r["year"], sign(r["cfo"]), sign(r["cfi"]),
                             sign(r["cff"]), label])
