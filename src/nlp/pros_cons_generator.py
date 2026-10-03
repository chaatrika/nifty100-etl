# pros_cons_generator.py - 12 pro rules and 12 con rules, with a confidence score (Sprint 5, Day 30)
#
# Run from the project root:   python -m src.nlp.pros_cons_generator
# Writes output/pros_cons_generated.csv   company_id, type, rule_id, text, confidence_pct
#
# Confidence = 50 + 50 x signal strength (0 to 1). Strength says how far past the threshold the
# company is (or how long the streak is). Only rules with confidence > 60 are written.

import os

import numpy as np
import pandas as pd

from src.analytics import series

OUT_FILE = os.path.join("output", "pros_cons_generated.csv")
MIN_CONFIDENCE = 60
FINANCIALS = "Financials"
ROE_MAX_TRUSTED = 150       # ROE above this comes from a tiny/negative equity base - not used for ROE rules


def clip(x):
    return float(min(max(x, 0.0), 1.0))


def confidence(strength):
    return round(50 + 50 * clip(strength), 1)


def vals(df, col, n=None):
    # the last n non-empty values of a column, oldest first
    s = df[col].dropna().tolist() if col in df else []
    return s if n is None else s[-n:]


def trailing_streak(values, test):
    # how many values at the END of the list pass test()
    n = 0
    for v in reversed(values):
        if test(v):
            n += 1
        else:
            break
    return n


def strictly(values, direction):
    if len(values) < 2:
        return False
    pairs = zip(values[:-1], values[1:])
    return all((b > a) if direction == "up" else (b < a) for a, b in pairs)


class Company:
    # everything the rules need for one company
    def __init__(self, cid, sector, ratios, pl, bs, mc):
        self.id, self.sector = cid, sector
        self.r, self.pl, self.bs = ratios, pl, bs
        self.is_fin = sector == FINANCIALS
        self.latest = ratios.iloc[-1] if len(ratios) else None
        self.div_yield = mc.sort_values("year")["dividend_yield_pct"].iloc[-1] if len(mc) else np.nan

    def last(self, col):
        if self.latest is None:
            return np.nan
        v = self.latest.get(col)
        return np.nan if v is None else v

    def roe_series(self):
        return [v for v in vals(self.r, "return_on_equity_pct")]


# ---------------- pro rules: each returns (strength, text) or None ----------------

def pro1(c):
    roe = vals(c.r, "return_on_equity_pct")
    n = trailing_streak(roe, lambda v: 20 < v <= ROE_MAX_TRUSTED)
    if n < 3:
        return None
    low = min(roe[-n:])
    return 0.5 * clip((low - 20) / 20) + 0.5 * clip((n - 3) / 4), \
        "Consistently high return on equity above 20% demonstrates exceptional capital efficiency"


def pro2(c):
    n = trailing_streak(vals(c.r, "free_cash_flow_cr"), lambda v: v > 0)
    if n < 5:
        return None
    return 0.3 + 0.7 * clip((n - 5) / 5), \
        "Strong free cash flow generation over 5 years signals healthy business fundamentals"


def debt_free(c):
    de, b = c.last("debt_to_equity"), np.nan
    if len(c.bs):
        b = c.bs["borrowings"].iloc[-1]
    return (pd.notna(b) and b <= 0) or (pd.notna(de) and de < 0.01)


def pro3(c):
    if not debt_free(c):
        return None
    return 0.9, "Debt-free balance sheet provides financial flexibility and eliminates interest burden"


def pro4(c):
    v = c.last("revenue_cagr_5yr")
    if pd.isna(v) or v <= 15:
        return None
    return clip((v - 15) / 15), "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum"


def pro5(c):
    v = c.last("operating_profit_margin_pct")
    if pd.isna(v) or v <= 25:
        return None
    return clip((v - 25) / 25), "Operating profit margin above 25% indicates strong pricing power and cost discipline"


def pro6(c):
    v = c.last("pat_cagr_5yr")
    if pd.isna(v) or v <= 20:
        return None
    return clip((v - 20) / 20), "Net profit compounding at above 20% over 5 years creates significant shareholder value"


def pro7(c):
    if c.is_fin:                     # interest coverage is not meaningful for banks/insurers
        return None
    text = "Very high interest coverage ratio reflects negligible financial stress from debt servicing"
    if debt_free(c):
        return 0.8, text
    icr = c.last("interest_coverage")
    if pd.isna(icr) or icr <= 10:
        return None
    return clip((icr - 10) / 40), text


def pro8(c):
    fcf = c.last("free_cash_flow_cr")
    if pd.isna(c.div_yield) or c.div_yield <= 2 or pd.isna(fcf) or fcf <= 0:
        return None
    return clip((c.div_yield - 2) / 4), "Consistent dividend yield above 2% backed by positive free cash flow"


def pro9(c):
    v = c.last("eps_cagr_5yr")
    if pd.isna(v) or v <= 15:
        return None
    return clip((v - 15) / 15), \
        "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding"


def pro10(c):
    roe = vals(c.r, "return_on_equity_pct", 4)
    if len(roe) < 4 or max(roe) > ROE_MAX_TRUSTED or not strictly(roe, "up"):
        return None
    return clip((roe[-1] - roe[0]) / 15), \
        "Return on equity improving for 3 consecutive years shows strengthening business quality"


def pro11(c):
    # the plan's title says "Revenue CAGR > PAT CAGR" but its text says revenue grows SLOWER than
    # profit, so we follow the text: PAT CAGR above revenue CAGR (both positive)
    rev, pat = c.last("revenue_cagr_5yr"), c.last("pat_cagr_5yr")
    if pd.isna(rev) or pd.isna(pat) or rev <= 0 or pat <= rev:
        return None
    return clip((pat - rev) / 10), \
        "Revenue growing slower than profits shows improving operating leverage and scale benefits"


def pro12(c):
    ta, bo = vals(c.bs, "total_assets", 2), vals(c.bs, "borrowings", 2)
    if len(ta) < 2 or len(bo) < 2 or ta[-1] <= ta[-2] or bo[-2] <= 0 or bo[-1] >= bo[-2]:
        return None
    growth, drop = (ta[-1] / ta[-2] - 1) * 100, (1 - bo[-1] / bo[-2]) * 100
    return 0.5 * clip(drop / 30) + 0.5 * clip(growth / 15), \
        "Growing asset base funded by internal accruals reflects self-sustaining growth"


# ---------------- con rules ----------------

def con1(c):
    de = c.last("debt_to_equity")
    if c.is_fin or pd.isna(de) or de <= 2.0:
        return None
    return clip((de - 2) / 3), (f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial "
                                "company and warrants monitoring")


def con2(c):
    n = trailing_streak(vals(c.r, "free_cash_flow_cr"), lambda v: v < 0)
    if n < 3:
        return None
    return 0.5 + 0.5 * clip((n - 3) / 3), \
        "Free cash flow negative for 3 consecutive years raises concern about cash generation quality"


def con3(c):
    opm = vals(c.r, "operating_profit_margin_pct", 4)
    if len(opm) < 4 or not strictly(opm, "down"):
        return None
    return clip((opm[0] - opm[-1]) / 10), \
        "Operating margins declining for 3 consecutive years suggest pricing or cost pressure"


def con4(c):
    npf = vals(c.pl, "net_profit", 1)
    if not npf or npf[-1] >= 0:
        return None
    return 0.8, "Company reported a net loss in the most recent financial year"


def con5(c):
    sales = vals(c.pl, "sales")
    k = 0
    for a, b in zip(reversed(sales[:-1]), reversed(sales[1:])):
        if b < a:
            k += 1
        else:
            break
    if k < 2:
        return None
    drop = (1 - sales[-1] / sales[-1 - k]) * 100
    return clip(0.4 + 0.2 * (k - 2) + drop / 40), \
        "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss"


def con6(c):
    icr = c.last("interest_coverage")
    if c.is_fin or pd.isna(icr) or icr >= 1.5 or debt_free(c):
        return None
    return clip((1.5 - icr) / 1.5), \
        "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations"


def con7(c):
    p = vals(c.pl, "dividend_payout", 1)
    if not p or p[-1] <= 100 or p[-1] > 5000:        # -999 style codes and absurd values are ignored
        return None
    return clip((p[-1] - 100) / 100), ("Dividend payout ratio above 100% means the company is paying "
                                       "dividends from reserves, which is unsustainable")


def con8(c):
    de = vals(c.r, "debt_to_equity", 4)
    if c.is_fin or len(de) < 4 or not strictly(de, "up"):
        return None
    return clip((de[-1] - de[0]) / 1.0), \
        "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk"


def con9(c):
    eps = vals(c.r, "earnings_per_share", 4)
    if len(eps) < 4 or not strictly(eps, "down") or eps[0] <= 0:
        return None
    return clip((1 - eps[-1] / eps[0]) / 0.4), \
        "Earnings per share declining for 3 consecutive years reflects deteriorating profitability"


def con10(c):
    v = c.last("return_on_capital_employed_pct")
    if c.is_fin or pd.isna(v) or v >= 10:
        return None
    return clip((10 - v) / 10), ("Return on capital employed below 10% suggests the business is not "
                                 "generating sufficient returns on invested capital")


def con11(c):
    nd, ebitda = c.last("net_debt_cr"), (vals(c.pl, "operating_profit", 1) or [np.nan])[-1]
    if c.is_fin or pd.isna(nd) or pd.isna(ebitda) or ebitda <= 0 or nd / ebitda <= 3:
        return None
    return clip((nd / ebitda - 3) / 4), ("Net debt exceeding 3 times EBITDA is a high leverage ratio "
                                         "and limits financial flexibility")


def con12(c):
    v = c.last("revenue_cagr_5yr")
    if pd.isna(v) or v >= 5:
        return None
    return clip((5 - v) / 10), "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum"


PRO_RULES = [(f"PRO{i}", f) for i, f in enumerate([pro1, pro2, pro3, pro4, pro5, pro6, pro7, pro8, pro9, pro10, pro11, pro12], 1)]
CON_RULES = [(f"CON{i}", f) for i, f in enumerate([con1, con2, con3, con4, con5, con6, con7, con8, con9, con10, con11, con12], 1)]


def evaluate(company):
    rows = []
    for kind, rules in (("pro", PRO_RULES), ("con", CON_RULES)):
        for rule_id, fn in rules:
            hit = fn(company)
            if hit is None:
                continue
            conf = confidence(hit[0])
            if conf > MIN_CONFIDENCE:
                rows.append((company.id, kind, rule_id, hit[1], conf))
    return rows


# ---------------- fallback: relative statements (only used when the 12 rules give nothing) ----------------
# A strong company can trigger none of the 12 con rules (and a weak one none of the 12 pro rules).
# So that every company still gets at least 1 pro and 1 con, we add ONE relative statement that compares
# the company with the Nifty 100 median. Rule ids PRO_REL / CON_REL make these easy to spot.

REL_METRICS = [  # (column, label, unit, higher_is_better, used_for_financials)
    ("return_on_equity_pct", "Return on equity", "%", True, True),
    ("return_on_capital_employed_pct", "Return on capital employed", "%", True, False),
    ("net_profit_margin_pct", "Net profit margin", "%", True, True),
    ("operating_profit_margin_pct", "Operating profit margin", "%", True, False),
    ("revenue_cagr_5yr", "5-year revenue CAGR", "%", True, True),
    ("pat_cagr_5yr", "5-year net profit CAGR", "%", True, True),
    ("asset_turnover", "Asset turnover", "x", True, False),
    ("debt_to_equity", "Debt-to-equity", "x", False, False),
]


def relative_statement(kind, company, universe, sectors):
    # kind = "pro" or "con". Picks the metric where the company is furthest above (pro) / below (con) the median.
    latest = universe.loc[universe["company_id"] == company.id]
    if latest.empty:
        return None
    row = latest.iloc[0]
    best = None
    for col, label, unit, higher_good, fin_ok in REL_METRICS:
        if company.is_fin and not fin_ok:
            continue
        v = row.get(col)
        med = universe.loc[universe["company_id"].map(sectors) != FINANCIALS, col].median() if not fin_ok \
            else universe[col].median()
        if pd.isna(v) or pd.isna(med):
            continue
        pct = (universe[col].dropna() < v).mean()                  # share of companies below this value
        good = pct if higher_good else 1 - pct                      # 1 = best of all, 0 = worst of all
        gap = good if kind == "pro" else 1 - good
        better = (v > med) if higher_good else (v < med)
        if (kind == "pro") != better:                                # need "better than median" for a pro, else worse
            continue
        if best is None or gap > best[0]:
            best = (gap, label, unit, v, med, higher_good)
    if best is None:
        return None
    gap, label, unit, v, med, higher_good = best
    above = (v > med) if higher_good else (v < med)
    if kind == "pro":
        word = "above" if higher_good else "below"
        text = f"{label} of {v:.1f}{unit} is {word} the Nifty 100 median of {med:.1f}{unit}"
    else:
        word = "below" if higher_good else "above"
        text = f"{label} of {v:.1f}{unit} is {word} the Nifty 100 median of {med:.1f}{unit}"
    return text, round(60 + 25 * gap, 1) if 60 + 25 * gap > 60 else 60.1


def generate(data=None):
    data = data or series.load_all()
    ratios, pl, bs = series.by_company(data["ratios"]), series.by_company(data["pl"]), series.by_company(data["bs"])
    mc = {k: g for k, g in data["mc"].groupby("company_id")}
    empty = pd.DataFrame()
    rows, companies = [], {}
    for r in data["companies"].itertuples():
        c = Company(r.company_id, r.sector, ratios.get(r.company_id, empty), pl.get(r.company_id, empty),
                    bs.get(r.company_id, empty), mc.get(r.company_id, empty))
        rows += evaluate(c)
        companies[r.company_id] = c

    out = pd.DataFrame(rows, columns=["company_id", "type", "rule_id", "text", "confidence_pct"])
    universe = data["ratios"].sort_values("fy").groupby("company_id").tail(1)
    sectors = dict(zip(data["companies"]["company_id"], data["companies"]["sector"]))
    extra = []
    for kind in ("pro", "con"):
        have = set(out.loc[out["type"] == kind, "company_id"])
        for cid, c in companies.items():
            if cid in have:
                continue
            hit = relative_statement(kind, c, universe, sectors)
            if hit is None and kind == "pro":
                # last resort for a pro: it made a profit in the latest year (plain fact, low confidence)
                npf, sal = vals(c.pl, "net_profit", 1), vals(c.pl, "sales", 1)
                if npf and sal and npf[-1] > 0:
                    hit = (f"Profitable in the latest financial year, with net profit of Rs {npf[-1]:,.0f} crore "
                           f"on sales of Rs {sal[-1]:,.0f} crore", 62.0)
            if hit:
                extra.append((cid, kind, kind.upper() + "_REL", hit[0], hit[1]))
    out = pd.concat([out, pd.DataFrame(extra, columns=out.columns)], ignore_index=True)
    return out.sort_values(["company_id", "type", "confidence_pct"], ascending=[True, True, False]).reset_index(drop=True)


def coverage(out, all_ids):
    have_pro = set(out.loc[out["type"] == "pro", "company_id"])
    have_con = set(out.loc[out["type"] == "con", "company_id"])
    return sorted(set(all_ids) - have_pro), sorted(set(all_ids) - have_con)


def main():
    data = series.load_all()
    out = generate(data)
    os.makedirs("output", exist_ok=True)
    out.to_csv(OUT_FILE, index=False)
    ids = data["companies"]["company_id"]
    no_pro, no_con = coverage(out, ids)
    print(f"{len(out)} lines for {out['company_id'].nunique()} of {len(ids)} companies "
          f"({(out['type'] == 'pro').sum()} pros, {(out['type'] == 'con').sum()} cons)")
    print("Companies with no pro:", no_pro or "none")
    print("Companies with no con:", no_con or "none")
    print(out.groupby(["type", "rule_id"]).size().to_string())


if __name__ == "__main__":
    main()
