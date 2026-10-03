# radar.py
# Radar (spider) charts for every company (Sprint 3, Day 19).
# - companies in a peer group: their shape + the peer group average as a dashed line
# - companies with no peer group: a small chart of their score against the Nifty 100 average
# Files go to reports/radar_charts/<company_id>_radar.png
#
# Run from the project root:   python -m src.analytics.radar

import os
import sqlite3
import re

import matplotlib
matplotlib.use("Agg")           # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.screener import engine as E

OUT_DIR = os.path.join("reports", "radar_charts")

# the 8 axes: (label, column in the scores table). All are on a 0 to 100 scale.
AXES = [
    ("ROE", "s_roe"),
    ("ROCE", "s_roce"),
    ("Net Profit\nMargin", "s_npm"),
    ("Low Debt\n(D/E)", "s_de"),
    ("FCF Score", "fcf_score"),
    ("PAT CAGR\n5yr", "s_pat_cagr"),
    ("Revenue CAGR\n5yr", "s_rev_cagr"),
    ("Composite\nScore", "composite_quality_score"),
]


def safe_name(company_id):
    return re.sub(r"[^A-Za-z0-9_-]", "_", company_id)


def prepare(df, config):
    # FCF score = the cash quality part of the composite score (FCF growth, CFO/PAT, FCF positive)
    w = config["composite_weights"]
    total = w["fcf_cagr_5yr"] + w["cfo_quality_score"] + w["fcf_positive"]
    df["fcf_score"] = (df["s_fcf_cagr"].fillna(0) * w["fcf_cagr_5yr"]
                       + df["s_cfo_quality"].fillna(0) * w["cfo_quality_score"]
                       + df["s_fcf_positive"].fillna(0) * w["fcf_positive"]) / total
    return df


def axis_values(row_or_df):
    values = []
    for label, column in AXES:
        v = row_or_df[column]
        values.append(0.0 if pd.isna(v) else float(v))
    return values


def draw_radar(name, group_name, company_values, peer_values, path):
    n = len(AXES)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles_closed = angles + angles[:1]

    fig, ax = plt.subplots(figsize=(7.5, 7.5), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    mine = company_values + company_values[:1]
    ax.plot(angles_closed, mine, color="#1F77B4", linewidth=2, label=name)
    ax.fill(angles_closed, mine, color="#1F77B4", alpha=0.30)

    avg = peer_values + peer_values[:1]
    ax.plot(angles_closed, avg, color="#D62728", linewidth=2, linestyle="--", label="Peer group average")

    ax.set_xticks(angles)
    ax.set_xticklabels([a[0] for a in AXES], fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=9, color="grey")
    ax.set_title(name + "\n" + group_name, fontsize=14, pad=40)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.12), fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def draw_standalone(name, company_score, nifty_avg, path):
    # for companies with no peer group: just compare the composite score with the Nifty 100 average
    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar([name, "Nifty 100 average"], [company_score, nifty_avg], color=["#1F77B4", "#AAAAAA"])
    for bar, value in zip(bars, [company_score, nifty_avg]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 1.5, "%.1f" % value,
                ha="center", fontsize=12)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Composite quality score (0-100)", fontsize=11)
    ax.set_title(name + " - no peer group assigned", fontsize=13)
    ax.tick_params(labelsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    config = E.load_config()
    conn = sqlite3.connect(E.DB_PATH)
    df = prepare(E.load_universe(conn), config)
    groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)
    conn.close()

    os.makedirs(OUT_DIR, exist_ok=True)
    group_of = dict(zip(groups["company_id"], groups["peer_group_name"]))
    nifty_avg = df["composite_quality_score"].mean()

    with_group = 0
    without_group = 0
    for i in range(len(df)):
        row = df.iloc[i]
        company_id = row["company_id"]
        label = row["company_name"] if isinstance(row["company_name"], str) else company_id
        path = os.path.join(OUT_DIR, safe_name(company_id) + "_radar.png")

        if company_id in group_of:
            group_name = group_of[company_id]
            members = df[df["company_id"].isin(groups[groups["peer_group_name"] == group_name]["company_id"])]
            peer_avg = [members[column].fillna(0).mean() for _, column in AXES]
            draw_radar(label, group_name, axis_values(row), peer_avg, path)
            with_group += 1
        else:
            draw_standalone(label, row["composite_quality_score"], nifty_avg, path)
            without_group += 1

    print("radar charts:", with_group, "with peer overlay,", without_group, "standalone ->", OUT_DIR)


if __name__ == "__main__":
    main()
