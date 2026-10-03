# cagr.py
# Growth rate (CAGR) calculations - Sprint 2, Day 10.
# CAGR = ((end / start) ^ (1 / years) - 1) x 100
# When the normal formula doesn't make sense we return None plus a flag saying why.

import math

OK = "OK"
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"   # positive -> negative
TURNAROUND = "TURNAROUND"             # negative -> positive
BOTH_NEGATIVE = "BOTH_NEGATIVE"       # negative -> negative
ZERO_BASE = "ZERO_BASE"               # started at zero
INSUFFICIENT = "INSUFFICIENT"         # not enough years of data


def to_num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(x):
        return None
    return x


def cagr(start, end, n_years):
    # returns (value, flag)
    start = to_num(start)
    end = to_num(end)

    if start is None or end is None or n_years is None or n_years <= 0:
        return None, INSUFFICIENT
    if start == 0:
        return None, ZERO_BASE
    if start > 0 and end < 0:
        return None, DECLINE_TO_LOSS
    if start < 0 and end > 0:
        return None, TURNAROUND
    if start < 0 and end <= 0:
        return None, BOTH_NEGATIVE

    # normal case: start is positive and end is zero or more
    value = ((end / start) ** (1.0 / n_years) - 1) * 100
    return value, OK


def cagr_from_series(series, window, end_year=None):
    # series is a dict like {2019: 100, 2020: 120, ...}
    # we take the end year (latest by default) and the value `window` years before it
    clean = {}
    for year, value in series.items():
        v = to_num(value)
        if v is not None:
            clean[int(year)] = v

    if len(clean) == 0:
        return None, INSUFFICIENT

    if end_year is None:
        end_year = max(clean)
    start_year = end_year - window

    if end_year not in clean or start_year not in clean:
        return None, INSUFFICIENT

    return cagr(clean[start_year], clean[end_year], window)


def all_cagrs(series, prefix, end_year=None, windows=(3, 5, 10)):
    # gives back a dict such as
    # {"revenue_cagr_3yr": 10.2, "revenue_cagr_3yr_flag": "OK", ...}
    result = {}
    for w in windows:
        value, flag = cagr_from_series(series, w, end_year)
        result[prefix + "_cagr_" + str(w) + "yr"] = value
        result[prefix + "_cagr_" + str(w) + "yr_flag"] = flag
    return result
