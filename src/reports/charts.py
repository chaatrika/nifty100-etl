# charts.py - matplotlib charts (drawn to PNG in memory) for the PDF reports
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.units import cm
from reportlab.platypus import Image

NAVY, TEAL, ORANGE, GREEN, RED = "#1F3864", "#2A9D8F", "#E76F51", "#2E7D32", "#C62828"
DPI = 150


def to_image(fig, width_cm, height_cm):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width_cm * cm, height=height_cm * cm)


def new_fig(width_cm, height_cm):
    fig, ax = plt.subplots(figsize=(width_cm / 2.54, height_cm / 2.54))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    return fig, ax


def no_data(width_cm, height_cm, title):
    fig, ax = new_fig(width_cm, height_cm)
    ax.axis("off")
    ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=9, color="grey")
    ax.set_title(title, fontsize=9, loc="left")
    return to_image(fig, width_cm, height_cm)


def years(df):
    return [str(int(y)) for y in df["fy"]]


def revenue_profit(pl, w, h):
    pl = pl.tail(10)
    if len(pl) == 0:
        return no_data(w, h, "Revenue and Net Profit (Rs Cr)")
    fig, ax = new_fig(w, h)
    x, bw = np.arange(len(pl)), 0.4
    ax.bar(x - bw / 2, pl["sales"], bw, label="Revenue", color=NAVY)
    ax.bar(x + bw / 2, pl["net_profit"].fillna(0), bw, label="Net profit", color=TEAL)
    ax.set_xticks(x, years(pl))
    ax.set_title("Revenue and Net Profit (Rs Cr)", fontsize=9, loc="left")
    ax.legend(fontsize=7, frameon=False)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    return to_image(fig, w, h)


def roe_roce(ratios, w, h):
    r = ratios.tail(10)
    if len(r) == 0:
        return no_data(w, h, "ROE and ROCE (%)")
    fig, ax = new_fig(w, h)
    x = np.arange(len(r))
    ax.plot(x, r["return_on_equity_pct"], marker="o", color=NAVY, label="ROE % (left)")
    ax.set_ylabel("ROE %", fontsize=7, color=NAVY)
    ax2 = ax.twinx()
    ax2.plot(x, r["return_on_capital_employed_pct"], marker="s", color=ORANGE, label="ROCE % (right)")
    ax2.set_ylabel("ROCE %", fontsize=7, color=ORANGE)
    ax2.tick_params(labelsize=7)
    ax2.spines[["top"]].set_visible(False)
    ax.set_xticks(x, years(r))
    ax.set_title("ROE (left axis) and ROCE (right axis)", fontsize=9, loc="left")
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [l.get_label() for l in lines], fontsize=7, frameon=False, loc="upper left")
    return to_image(fig, w, h)


def balance_sheet(bs, w, h):
    bs = bs.tail(10)
    if len(bs) == 0:
        return no_data(w, h, "Balance sheet composition (Rs Cr)")
    fig, ax = new_fig(w, h)
    x = np.arange(len(bs))
    equity = (bs["equity_capital"].fillna(0) + bs["reserves"].fillna(0)).to_numpy()
    borrow = bs["borrowings"].fillna(0).to_numpy()
    other = bs["other_liabilities"].fillna(0).to_numpy()
    ax.bar(x, equity, label="Equity", color=NAVY)
    ax.bar(x, borrow, bottom=equity, label="Borrowings", color=ORANGE)
    ax.bar(x, other, bottom=equity + borrow, label="Other liabilities", color="#9CA3AF")
    ax.set_xticks(x, years(bs), rotation=45)
    ax.set_title("Balance sheet composition (Rs Cr)", fontsize=9, loc="left")
    ax.legend(fontsize=6, frameon=False)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    return to_image(fig, w, h)


def cash_flow_waterfall(cf, w, h):
    if len(cf) == 0:
        return no_data(w, h, "Cash flow waterfall")
    last = cf.iloc[-1]
    cfo, cfi, cff = (float(last[c]) if last[c] == last[c] else 0.0
                     for c in ("operating_activity", "investing_activity", "financing_activity"))
    net = float(last["net_cash_flow"]) if last["net_cash_flow"] == last["net_cash_flow"] else cfo + cfi + cff
    fig, ax = new_fig(w, h)
    starts, heights = [0, cfo, cfo + cfi, 0], [cfo, cfi, cff, net]
    cols = [GREEN if v >= 0 else RED for v in heights[:3]] + [NAVY]
    ax.bar(["CFO", "CFI", "CFF", "Net cash flow"], heights, bottom=starts, color=cols)
    ax.axhline(0, color="black", lw=0.6)
    levels = [0, cfo, cfo + cfi, cfo + cfi + cff, net]
    lo, hi = min(levels), max(levels)
    pad = (hi - lo) * 0.18 or 1.0
    ax.set_ylim(lo - pad, hi + pad * 1.4)     # room for the value labels and the title
    span = pad * 0.15
    for i, (s0, hgt) in enumerate(zip(starts, heights)):
        ax.text(i, max(s0, s0 + hgt) + span, f"{hgt:,.0f}", ha="center", fontsize=6.5)
    ax.set_title(f"Cash flow, FY{int(last['fy'])} (Rs Cr)", fontsize=9, loc="left")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    return to_image(fig, w, h)
