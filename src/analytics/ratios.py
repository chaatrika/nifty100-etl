# ratios.py
# Profit, debt and efficiency ratios for the Nifty 100 project (Sprint 2, Day 08 and 09).
# If a ratio can't be worked out (zero or negative bottom number) we return None
# instead of a wrong value.

import logging
import math

log = logging.getLogger("ratio_edge_cases")

FINANCIAL_SECTOR = "Financials"


def to_num(x):
    # turn blanks / NaN into None, everything else into a float
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(x):
        return None
    return x


def safe_divide(a, b):
    a = to_num(a)
    b = to_num(b)
    if a is None or b is None or b == 0:
        return None
    return a / b


# ---------------- Day 08 : profitability ----------------

def net_profit_margin(net_profit, sales):
    # net profit / sales x 100
    result = safe_divide(net_profit, sales)
    if result is None:
        return None
    return result * 100


def operating_profit_margin(operating_profit, sales):
    result = safe_divide(operating_profit, sales)
    if result is None:
        return None
    return result * 100


def opm_mismatch(computed, reported, tolerance=1.0, company_id=None, year=None):
    # compare our OPM with the opm_percentage from the file
    # if they are more than 1 point apart, log it and return True
    computed = to_num(computed)
    reported = to_num(reported)
    if computed is None or reported is None:
        return False
    diff = abs(computed - reported)
    if diff > tolerance:
        log.warning("OPM_MISMATCH company=%s year=%s computed=%.2f reported=%.2f diff=%.2f",
                    company_id, year, computed, reported, diff)
        return True
    return False


def return_on_equity(net_profit, equity_capital, reserves):
    # net profit / (equity capital + reserves) x 100
    net_worth = (to_num(equity_capital) or 0) + (to_num(reserves) or 0)
    if net_worth <= 0:
        return None
    result = safe_divide(net_profit, net_worth)
    if result is None:
        return None
    return result * 100


def return_on_capital_employed(ebit, equity_capital, reserves, borrowings):
    # EBIT / (equity + reserves + borrowings) x 100
    capital = (to_num(equity_capital) or 0) + (to_num(reserves) or 0) + (to_num(borrowings) or 0)
    if capital <= 0:
        return None
    result = safe_divide(ebit, capital)
    if result is None:
        return None
    return result * 100


def roce_vs_sector(roce, sector_median_roce):
    # for banks / financial companies we compare with the sector median
    # instead of using one fixed number
    roce = to_num(roce)
    median = to_num(sector_median_roce)
    if roce is None or median is None:
        return None
    if roce >= median:
        return "Above Sector"
    return "Below Sector"


def return_on_assets(net_profit, total_assets):
    result = safe_divide(net_profit, total_assets)
    if result is None:
        return None
    return result * 100


# ---------------- Day 09 : debt and efficiency ----------------

def debt_to_equity(borrowings, equity_capital, reserves):
    b = to_num(borrowings)
    # no borrowings means D/E is 0 (not None)
    if b is not None and b == 0:
        return 0.0
    net_worth = (to_num(equity_capital) or 0) + (to_num(reserves) or 0)
    if b is None or net_worth <= 0:
        return None
    return b / net_worth


def high_leverage_flag(de, broad_sector):
    # True when D/E is above 5, but not for banks (they always have high debt)
    de = to_num(de)
    if de is None:
        return False
    if broad_sector == FINANCIAL_SECTOR:
        return False
    return de > 5


def interest_coverage(operating_profit, other_income, interest):
    # (operating profit + other income) / interest
    # no interest = debt free company, so we return None
    i = to_num(interest)
    if i is None or i == 0:
        return None
    top = (to_num(operating_profit) or 0) + (to_num(other_income) or 0)
    return top / i


def icr_label(icr, interest):
    # show "Debt Free" when the company pays no interest
    i = to_num(interest)
    if i is not None and i == 0:
        return "Debt Free"
    return None


def icr_warning_flag(icr):
    # True when coverage is below 1.5 (may struggle to pay interest)
    icr = to_num(icr)
    if icr is None:
        return False
    return icr < 1.5


def net_debt(borrowings, investments):
    # borrowings - investments (investments used as the cash-like amount)
    b = to_num(borrowings)
    inv = to_num(investments)
    if b is None:
        return None
    if inv is None:
        inv = 0
    return b - inv


def asset_turnover(sales, total_assets):
    return safe_divide(sales, total_assets)
