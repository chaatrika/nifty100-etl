# clustering.py
# Groups the 92 companies into 5 archetypes using KMeans (Sprint 6, Day 36-37).
#
# Run from the project root:   python -m src.analytics.clustering
#
# Writes:
#   output/cluster_labels.csv          company_id, cluster_id, cluster_name, distance_from_centroid
#   output/portfolio_stats.csv         P10-P90, mean, std for the core KPIs
#   output/outlier_report.csv          companies with |Z-score| > 3 within their sector
#   reports/elbow_plot.png             inertia vs k, to check k=5 is a reasonable choice
#   reports/correlation_heatmap.png    Pearson correlation of 10 KPIs

import os
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_PATH = os.path.join("data", "nifty100.db")
OUT_DIR = "output"
REPORT_DIR = "reports"

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

# the 10 KPIs used for the correlation heatmap and the portfolio stats table
PORTFOLIO_KPIS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "free_cash_flow_cr",
]

N_CLUSTERS = 5
RANDOM_STATE = 42


def load_latest(conn):
    # one row per company: the latest year with real profit data, plus FCF 5yr CAGR
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr = fr[fr["net_profit_margin_pct"].notna()].copy()
    fr["fy"] = fr["year"].str[:4].astype(int)
    fr = fr.sort_values(["company_id", "year"]).drop_duplicates(
        ["company_id", "fy"], keep="last"
    )

    # FCF 5yr CAGR, using the same helper the screener uses
    from src.analytics import cagr as C

    rows = []
    for company_id, g in fr.groupby("company_id"):
        g = g.reset_index(drop=True)
        latest = g.iloc[-1].to_dict()
        series = {
            fy: v for fy, v in zip(g["fy"], g["free_cash_flow_cr"]) if pd.notna(v)
        }
        value, _ = C.cagr_from_series(series, 5, end_year=latest["fy"])
        latest["fcf_cagr_5yr"] = value
        rows.append(latest)
    df = pd.DataFrame(rows)

    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    names = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
    df = df.merge(sectors, on="company_id", how="left").merge(
        names, on="company_id", how="left"
    )
    return df


def impute_by_sector(df, columns):
    # missing values get the median of the same column within the same sector
    # (or the whole-universe median, if the sector itself has no value for that column)
    out = df.copy()
    for col in columns:
        overall_median = out[col].median()
        sector_median = out.groupby("broad_sector")[col].transform("median")
        sector_median = sector_median.fillna(overall_median)
        out[col] = out[col].fillna(sector_median)
    return out


def run_kmeans(df, k=N_CLUSTERS):
    X = df[FEATURES].to_numpy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    labels = model.fit_predict(X_scaled)
    distances = np.linalg.norm(X_scaled - model.cluster_centers_[labels], axis=1)
    return labels, distances, model, scaler, X_scaled


def elbow_plot(X_scaled, path, k_max=10):
    inertias = []
    ks = list(range(2, k_max + 1))
    for k in ks:
        model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        model.fit(X_scaled)
        inertias.append(model.inertia_)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(ks, inertias, marker="o", color="#1F77B4")
    ax.axvline(5, color="red", linestyle="--", label="k = 5 (chosen)")
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel("Inertia (within-cluster sum of squares)")
    ax.set_title("Elbow plot for KMeans clustering")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return dict(zip(ks, inertias))


def name_clusters(df, labels):
    # look at the average profile of each cluster and pick the closest-fitting name.
    # A person should sanity check these names against the actual member companies.
    df = df.copy()
    df["cluster_id"] = labels
    profile = df.groupby("cluster_id")[FEATURES].mean()

    candidates = [
        "High-Quality Compounders",  # high ROE, low debt, decent growth
        "Defensive Dividend Payers",  # steady but modest growth, low debt
        "Value Cyclicals",  # average returns, more debt, cyclical margins
        "Distressed or Turnaround",  # weak ROE, high debt, weak or negative growth
        "Emerging Growth",  # high revenue growth, lower current margins
    ]

    # score each cluster against a simple rule set, then assign the best-fitting
    # name to the highest scoring cluster first, so names are not reused
    scores = pd.DataFrame(index=profile.index)
    scores["High-Quality Compounders"] = (
        profile["return_on_equity_pct"].rank() - profile["debt_to_equity"].rank()
    )
    scores["Defensive Dividend Payers"] = (
        -profile["debt_to_equity"].rank() - profile["revenue_cagr_5yr"].rank()
    )
    scores["Value Cyclicals"] = (
        profile["debt_to_equity"].rank()
        - profile["revenue_cagr_5yr"]
        .rank()
        .sub(profile["revenue_cagr_5yr"].rank().mean())
        .abs()
    )
    scores["Distressed or Turnaround"] = (
        -profile["return_on_equity_pct"].rank() + profile["debt_to_equity"].rank()
    )
    scores["Emerging Growth"] = (
        profile["revenue_cagr_5yr"].rank()
        - profile["operating_profit_margin_pct"].rank()
    )

    assigned = {}
    remaining_clusters = list(profile.index)
    remaining_names = list(candidates)
    while remaining_names:
        name = remaining_names[0]
        best_cluster = max(remaining_clusters, key=lambda c: scores.loc[c, name])
        assigned[best_cluster] = name
        remaining_clusters.remove(best_cluster)
        remaining_names.remove(name)

    return df["cluster_id"].map(assigned), profile, assigned


def cluster_profile_table(df):
    return (
        df.groupby(["cluster_id", "cluster_name"])[FEATURES]
        .agg(["mean", "median"])
        .round(2)
    )


def correlation_heatmap(df, path):
    corr = df[PORTFOLIO_KPIS].corr(method="pearson")
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        ax=ax,
        cbar_kws={"label": "Pearson correlation"},
    )
    ax.set_title("Correlation of core KPIs (latest year, all companies)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return corr


def portfolio_stats(df):
    rows = []
    for col in PORTFOLIO_KPIS:
        s = df[col].dropna()
        rows.append(
            {
                "metric": col,
                "count": len(s),
                "p10": s.quantile(0.10),
                "p25": s.quantile(0.25),
                "p50": s.quantile(0.50),
                "p75": s.quantile(0.75),
                "p90": s.quantile(0.90),
                "mean": s.mean(),
                "std": s.std(),
            }
        )
    return pd.DataFrame(rows).round(2)


def outlier_report(df):
    # Z-score of each metric within the company's own sector; |Z| > 3 gets flagged.
    rows = []
    for col in PORTFOLIO_KPIS:
        for sector, group in df.groupby("broad_sector"):
            values = group[col]
            std = values.std()
            if pd.isna(std) or std == 0:
                continue
            z = (values - values.mean()) / std
            for company_id, zscore in z.items():
                if pd.notna(zscore) and abs(zscore) > 3:
                    rows.append(
                        {
                            "company_id": df.loc[company_id, "company_id"],
                            "broad_sector": sector,
                            "metric": col,
                            "value": round(float(values[company_id]), 2),
                            "z_score": round(float(zscore), 2),
                        }
                    )
    return pd.DataFrame(
        rows, columns=["company_id", "broad_sector", "metric", "value", "z_score"]
    )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    df = load_latest(conn)
    conn.close()

    df = impute_by_sector(df, FEATURES)
    labels, distances, model, scaler, X_scaled = run_kmeans(df)
    df["cluster_id"] = labels
    df["distance_from_centroid"] = np.round(distances, 3)
    df["cluster_name"], profile, name_map = name_clusters(df, labels)

    labels_out = df[
        ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    ]
    labels_out.to_csv(os.path.join(OUT_DIR, "cluster_labels.csv"), index=False)

    inertias = elbow_plot(X_scaled, os.path.join(REPORT_DIR, "elbow_plot.png"))
    correlation_heatmap(
        df.set_index("company_id"), os.path.join(REPORT_DIR, "correlation_heatmap.png")
    )

    portfolio_stats(df).to_csv(
        os.path.join(OUT_DIR, "portfolio_stats.csv"), index=False
    )
    outliers = outlier_report(df.set_index("company_id", drop=False))
    outliers.to_csv(os.path.join(OUT_DIR, "outlier_report.csv"), index=False)

    print("clusters:", df["cluster_id"].nunique(), "| companies:", len(df))
    print(df["cluster_name"].value_counts().to_string())
    print("elbow inertia at k=4,5,6:", inertias[4], inertias[5], inertias[6])
    print("outliers flagged:", len(outliers))


if __name__ == "__main__":
    main()
