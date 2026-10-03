# engine.py
# The screener: loads the latest numbers for every company, applies the filters
# from config/screener_config.yaml, and works out the composite quality score.
# (Sprint 3, Day 15 to 17)

import os
import sqlite3

import numpy as np
import pandas as pd
import yaml

from src.analytics import cagr as C

DB_PATH = os.path.join("data", "nifty100.db")
CONFIG_PATH = os.path.join("config", "screener_config.yaml")
FINANCIALS = "Financials"

# filter name -> (column, "min" or "max")
FILTERS = {
    "roe_min": ("return_on_equity_pct", "min"),
    "de_max": ("debt_to_equity", "max"),
    "fcf_min": ("free_cash_flow_cr", "min"),
    "revenue_cagr_5yr_min": ("revenue_cagr_5yr", "min"),
    "pat_cagr_5yr_min": ("pat_cagr_5yr", "min"),
    "opm_min": ("operating_profit_margin_pct", "min"),
    "pe_max": ("pe_ratio", "max"),
    "pb_max": ("pb_ratio", "max"),
    "dividend_yield_min": ("dividend_yield_pct", "min"),
    "icr_min": ("interest_coverage", "min"),
    "market_cap_min": ("market_cap_crore", "min"),
    "net_profit_min": ("net_profit_cr", "min"),
    "eps_cagr_min": ("eps_cagr_5yr", "min"),
    "asset_turnover_min": ("asset_turnover", "min"),
    "sales_min": ("sales_cr", "min"),
    # extra ones used by the presets
    "dividend_payout_max": ("dividend_payout_ratio_pct", "max"),
    "revenue_cagr_3yr_min": ("revenue_cagr_3yr", "min"),
}
# yes/no filters
SPECIAL_FILTERS = ["fcf_positive_latest", "de_declining"]

# the 20 KPI columns shown in the Excel reports
KPI_COLUMNS = [
    "composite_quality_score",
    "sector_relative_score",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "revenue_cagr_3yr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "dividend_payout_ratio_pct",
    "market_cap_crore",
    "sales_cr",
    "net_profit_cr",
]

# which score column belongs to which metric (used by the composite score)
SCORE_COLS = {
    "return_on_equity_pct": "s_roe",
    "return_on_capital_employed_pct": "s_roce",
    "net_profit_margin_pct": "s_npm",
    "fcf_cagr_5yr": "s_fcf_cagr",
    "cfo_quality_score": "s_cfo_quality",
    "fcf_positive": "s_fcf_positive",
    "revenue_cagr_5yr": "s_rev_cagr",
    "pat_cagr_5yr": "s_pat_cagr",
    "debt_to_equity": "s_de",
    "interest_coverage": "s_icr",
}


def load_config(path=CONFIG_PATH):
    f = open(path)
    config = yaml.safe_load(f)
    f.close()
    return config


# ---------------- loading the data ----------------


def load_universe(conn):
    # one row per company: the latest year that has profit data
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr = fr[fr["net_profit_margin_pct"].notna()].copy()
    fr["fy"] = fr["year"].str[:4].astype(int)
    fr = fr.sort_values(["company_id", "year"])

    rows = []
    for company_id, group in fr.groupby("company_id"):
        group = group.reset_index(drop=True)
        latest = group.iloc[-1].to_dict()

        # D/E of the year before (for the "D/E declining" filter)
        latest["de_prev"] = group.iloc[-2]["debt_to_equity"] if len(group) > 1 else None

        # FCF growth over 5 years (FCF can be negative, so the cagr flags matter here)
        fcf_series = {}
        for fy, v in zip(group["fy"], group["free_cash_flow_cr"]):
            if pd.notna(v):
                fcf_series[fy] = v
        value, flag = C.cagr_from_series(fcf_series, 5, end_year=latest["fy"])
        latest["fcf_cagr_5yr"] = value
        rows.append(latest)
    df = pd.DataFrame(rows)

    # sales and net profit in crore, from the profit and loss table
    pl = pd.read_sql(
        "SELECT company_id, year, sales AS sales_cr, net_profit AS net_profit_cr "
        "FROM profitandloss",
        conn,
    )
    df = df.merge(pl, on=["company_id", "year"], how="left")

    # market data (latest year for each company)
    mc = pd.read_sql("SELECT * FROM market_cap", conn)
    mc = mc.sort_values("year").groupby("company_id").tail(1)
    mc = mc[
        ["company_id", "market_cap_crore", "pe_ratio", "pb_ratio", "dividend_yield_pct"]
    ]
    df = df.merge(mc, on="company_id", how="left")

    names = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    df = df.merge(names, on="company_id", how="left").merge(
        sectors, on="company_id", how="left"
    )

    # debt free companies have no interest, so the ratio is empty.
    # For screening we treat them as "infinite" coverage.
    df["icr_for_filter"] = df["interest_coverage"]
    debt_free = df["icr_label"] == "Debt Free"
    df.loc[debt_free, "icr_for_filter"] = np.inf

    df = add_scores(df)
    return df.sort_values("composite_quality_score", ascending=False).reset_index(
        drop=True
    )


# ---------------- composite score ----------------


def winsor_scale(series, lower_is_better=False, low_q=0.10, high_q=0.90):
    # cap the values at the 10th and 90th percentile, then scale to 0-100.
    finite = series.replace([np.inf, -np.inf], np.nan)
    if finite.notna().sum() == 0:
        return pd.Series(np.nan, index=series.index)
    low = finite.quantile(low_q)
    high = finite.quantile(high_q)
    if high == low:
        scaled = pd.Series(50.0, index=series.index)
        scaled[series.isna()] = np.nan
    else:
        clipped = series.clip(low, high)  # inf becomes "high"
        scaled = (clipped - low) / (high - low) * 100
    if lower_is_better:
        scaled = 100 - scaled
    return scaled


def score_metrics(df, config):
    # gives a table of 0-100 scores (one column per metric) for the companies in df
    low_q = config.get("winsor_low", 0.10)
    high_q = config.get("winsor_high", 0.90)
    s = pd.DataFrame(index=df.index)

    s["s_roe"] = winsor_scale(df["return_on_equity_pct"], False, low_q, high_q)
    s["s_roce"] = winsor_scale(
        df["return_on_capital_employed_pct"], False, low_q, high_q
    )
    s["s_npm"] = winsor_scale(df["net_profit_margin_pct"], False, low_q, high_q)
    s["s_fcf_cagr"] = winsor_scale(df["fcf_cagr_5yr"], False, low_q, high_q)
    s["s_cfo_quality"] = winsor_scale(df["cfo_quality_score"], False, low_q, high_q)
    s["s_rev_cagr"] = winsor_scale(df["revenue_cagr_5yr"], False, low_q, high_q)
    s["s_pat_cagr"] = winsor_scale(df["pat_cagr_5yr"], False, low_q, high_q)
    s["s_de"] = winsor_scale(df["debt_to_equity"], True, low_q, high_q)
    s["s_icr"] = winsor_scale(df["icr_for_filter"], False, low_q, high_q)

    # FCF positive flag: 100 if free cash flow is above zero, else 0
    s["s_fcf_positive"] = np.where(df["free_cash_flow_cr"] > 0, 100.0, 0.0)
    return s


def points_to_score(scores, config):
    # add up the weighted scores. A metric with no value gets 0 points.
    weights = config["composite_weights"]
    total_weight = sum(weights.values())
    total = pd.Series(0.0, index=scores.index)
    for metric, weight in weights.items():
        col = SCORE_COLS[metric]
        total = total + scores[col].fillna(0) * weight
    return total / total_weight


def add_scores(df, config=None):
    if config is None:
        config = load_config()

    # 1. score against the whole universe
    scores = score_metrics(df, config)

    # leverage is not comparable for banks (high debt is normal), so they get a neutral 50
    is_bank = df["broad_sector"] == FINANCIALS
    scores.loc[is_bank, "s_de"] = 50.0
    scores.loc[is_bank, "s_icr"] = 50.0

    for col in scores.columns:
        df[col] = scores[col]
    df["composite_quality_score"] = points_to_score(scores, config).round(1)

    # 2. score against the company's own sector
    min_size = config.get("min_sector_size", 5)
    sector_score = pd.Series(np.nan, index=df.index)
    for sector, group in df.groupby("broad_sector"):
        if len(group) < min_size:
            # too few companies to compare, use the universe score
            sector_score[group.index] = df.loc[group.index, "composite_quality_score"]
            continue
        sector_scores = score_metrics(group, config)
        sector_score[group.index] = points_to_score(sector_scores, config).round(1)
    df["sector_relative_score"] = sector_score
    return df


# ---------------- filters ----------------


def check_filters(df, filters, skip_financials_de=True):
    # returns a True/False table: one column per filter, one row per company
    result = pd.DataFrame(index=df.index)
    is_bank = df["broad_sector"] == FINANCIALS

    for name, value in filters.items():
        if name in FILTERS:
            column, kind = FILTERS[name]
            if name == "icr_min":
                data = df["icr_for_filter"]  # debt free = infinity, always passes
            else:
                data = df[column]
            if kind == "min":
                ok = data >= value
            else:
                ok = data <= value
            ok = ok.fillna(False)  # missing value = can't confirm = fail
            if name == "de_max" and skip_financials_de:
                ok = ok | is_bank  # banks skip the D/E filter
            result[name] = ok

        elif name == "fcf_positive_latest":
            ok = (df["free_cash_flow_cr"] > 0).fillna(False)
            result[name] = ok if value else ~ok

        elif name == "de_declining":
            ok = (df["debt_to_equity"] < df["de_prev"]).fillna(False)
            if skip_financials_de:
                ok = ok | is_bank
            result[name] = ok if value else ~ok

        else:
            raise ValueError("Unknown filter: " + name)
    return result


def apply_filters(df, filters, exclude_sectors=None):
    # keep only the companies that pass every filter, best composite score first
    data = df
    if exclude_sectors:
        data = data[~data["broad_sector"].isin(exclude_sectors)]
    checks = check_filters(data, filters)
    passed = data[checks.all(axis=1)] if len(checks.columns) > 0 else data
    return passed.sort_values("composite_quality_score", ascending=False)


def run_preset(df, config, preset_name):
    preset = config["presets"][preset_name]
    return apply_filters(df, preset["filters"], preset.get("exclude_sectors"))


def run_all_presets(df, config):
    results = {}
    for name in config["presets"]:
        results[name] = run_preset(df, config, name)
    return results


def run_custom(df, filters):
    # your own thresholds, e.g. run_custom(df, {"roe_min": 18, "de_max": 0.5})
    return apply_filters(df, filters)


def get_universe(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    df = load_universe(conn)
    conn.close()
    return df
