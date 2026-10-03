# tearsheet.py - the 2-page company tearsheet PDF (Sprint 5, Day 33 and 34)
#
# Run from the project root:
#   python -m src.reports.tearsheet                    all companies -> reports/tearsheets/<TICKER>_tearsheet.pdf
#   python -m src.reports.tearsheet TCS HDFCBANK       only these tickers
#
# Companies with no profit and loss data are skipped and listed in
# output/skipped_tearsheets.csv.

import os
import sys

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepInFrame, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

from src.reports import charts
from src.reports.common import GREEN, GREY, LIGHT, NAVY, RED, esc, fmt, latest, load_bundle, safe_name

OUT_DIR = os.path.join("reports", "tearsheets")
MIN_YEARS = 1          # a company is skipped only when it has no P&L data at all
LIMITED_YEARS = 3      # fewer years than this -> tearsheet carries a "limited history" note
MARGIN = 1.5 * cm
W = A4[0] - 2 * MARGIN                 # usable width
H = A4[1] - 2 * MARGIN - 0.6 * cm      # usable height (a little spare so the frame never overflows)
MAX_LINES = 5                          # pros / cons shown per company

base = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("t", parent=base["Title"], textColor=colors.white, fontSize=18, leading=22, alignment=0),
    "sub": ParagraphStyle("s", parent=base["Normal"], textColor=colors.white, fontSize=9, leading=12),
    "label": ParagraphStyle("l", parent=base["Normal"], textColor=GREY, fontSize=8, leading=10, alignment=TA_CENTER),
    "value": ParagraphStyle("v", parent=base["Normal"], textColor=NAVY, fontSize=16, leading=19, alignment=TA_CENTER,
                            fontName="Helvetica-Bold"),
    "h": ParagraphStyle("h", parent=base["Heading3"], fontSize=11, spaceBefore=4, spaceAfter=3),
    "bullet": ParagraphStyle("b", parent=base["Normal"], fontSize=8.5, leading=11, leftIndent=12, bulletIndent=0,
                             spaceAfter=2),
    "small": ParagraphStyle("sm", parent=base["Normal"], fontSize=7, leading=9, textColor=GREY),
    "badge": ParagraphStyle("bd", parent=base["Normal"], textColor=colors.white, fontSize=10, leading=13,
                            alignment=TA_CENTER, fontName="Helvetica-Bold"),
}

PATTERN_NOTE = {
    "Shareholder Returns": "Strong operating cash flow is being returned to shareholders and lenders.",
    "Reinvestor": "Operating cash flow is being reinvested in the business.",
    "Growth Funded by Debt": "Growth spending is funded by outside financing.",
    "Liquidating Assets": "Cash is coming from selling assets while debt is repaid.",
    "Mixed": "Cash flow signs do not fit one clear pattern.",
    "Distress Signal": "Operations burn cash while financing and asset sales fill the gap.",
    "Cash Accumulator": "All three cash flows are positive and cash is piling up.",
    "Pre-Revenue": "All three cash flows are negative.",
}


def header(name, ticker, sector, sub_sector):
    t = Table([[Paragraph(esc(name), S["title"])],
               [Paragraph(f"{esc(ticker)}  |  {esc(sector)}  |  {esc(sub_sector)}", S["sub"])]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, -1), (-1, -1), 8)]))
    return t


def kpi_tiles(ratios):
    r = ratios
    items = [("ROE", fmt(latest(r, "return_on_equity_pct"), "%")),
             ("ROCE", fmt(latest(r, "return_on_capital_employed_pct"), "%")),
             ("Net profit margin", fmt(latest(r, "net_profit_margin_pct"), "%")),
             ("Debt to equity", fmt(latest(r, "debt_to_equity"), "", 2)),
             ("Revenue CAGR 5yr", fmt(latest(r, "revenue_cagr_5yr"), "%")),
             ("Free cash flow (Rs Cr)", fmt(latest(r, "free_cash_flow_cr"), "", 0))]
    cells = [[Paragraph(esc(l), S["label"]), Spacer(1, 2), Paragraph(esc(v), S["value"])] for l, v in items]
    t = Table([cells[:3], cells[3:]], colWidths=[W / 3] * 3, rowHeights=[1.9 * cm] * 2)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.lightgrey), ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.white),
                           ("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def bullets(rows, color, empty):
    if rows is None or len(rows) == 0:
        return [Paragraph(empty, S["small"])]
    out = []
    for r in rows.sort_values("confidence_pct", ascending=False).head(MAX_LINES).itertuples():
        out.append(Paragraph(f'<font color="{color}">{esc(r.text)}</font> <font color="#6B7280" size="7">({r.confidence_pct:.0f}%)</font>',
                             S["bullet"], bulletText="•"))
    return out


def build_story(cid, b):
    info = b["companies"].loc[cid]
    r, pl, bs, cf = b["ratios"].get(cid), b["pl"].get(cid), b["bs"].get(cid), b["cf"].get(cid)
    empty = pd.DataFrame({"fy": []})
    r, pl, bs, cf = (x if x is not None else empty for x in (r, pl, bs, cf))
    year = int(r["fy"].iloc[-1]) if len(r) else "N/A"
    n_years = len(pl)
    limited = ([Paragraph(f"Limited history: only {n_years} year(s) of data available, so multi-year figures "
                          f"(CAGR, trends) may be N/A or less reliable.", S["small"]), Spacer(1, 4)]
               if n_years < LIMITED_YEARS else [])

    # ---- page 1
    p1 = [header(info["company_name"], cid, info["sector"] or "N/A", info["sub_sector"] or "N/A"), Spacer(1, 8),
          *limited, Paragraph(f"Key figures, financial year {year}", S["h"]), kpi_tiles(r), Spacer(1, 8),
          charts.revenue_profit(pl, 17.5, 6.6), Spacer(1, 6), charts.roe_roce(r, 17.5, 6.6)]

    # ---- page 2
    pc = b["pros_cons"].get(cid)
    pros = pc[pc["type"] == "pro"] if pc is not None else None
    cons = pc[pc["type"] == "con"] if pc is not None else None
    row = Table([[charts.balance_sheet(bs, 8.6, 7.6), charts.cash_flow_waterfall(cf, 8.6, 7.6)]], colWidths=[W / 2] * 2)
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    pattern = b["pattern"].get(cid, "N/A")
    badge = Table([[Paragraph(f"Capital allocation: {esc(pattern)}", S["badge"])]], colWidths=[W])
    badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("TOPPADDING", (0, 0), (-1, -1), 6),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    p2 = [header(info["company_name"], cid, info["sector"] or "N/A", info["sub_sector"] or "N/A"), Spacer(1, 8), row,
          Spacer(1, 6), Paragraph('<font color="#2E7D32">Pros</font>', S["h"]),
          *bullets(pros, "#2E7D32", "No pros generated."), Spacer(1, 4),
          Paragraph('<font color="#C62828">Cons</font>', S["h"]), *bullets(cons, "#C62828", "No cons generated."),
          Spacer(1, 6), badge, Spacer(1, 3), Paragraph(esc(PATTERN_NOTE.get(pattern, "")), S["small"]),
          Spacer(1, 6), Paragraph("Generated from the Nifty 100 database. Percentages in brackets are the rule confidence. "
                                  "Pros and cons are automatic and are not investment advice. Market data (stock prices, market cap, P/E, P/B) used anywhere in this project is SIMULATED.", S["small"])]

    # KeepInFrame(shrink) guarantees each page's content stays inside its page: no overflow, no 3rd page
    return [KeepInFrame(W, H, p1, mode="shrink"), PageBreak(), KeepInFrame(W, H, p2, mode="shrink")]


def make_tearsheet(cid, b, out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{safe_name(cid)}_tearsheet.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                            bottomMargin=MARGIN, title=f"{cid} tearsheet", author="Nifty 100 Analytics")
    doc.build(build_story(cid, b))
    return path


def run_batch(tickers=None, out_dir=OUT_DIR):
    b = load_bundle()
    ids = tickers or list(b["companies"].index)
    skipped, made = [], []
    for cid in ids:
        if cid not in b["companies"].index:
            skipped.append((cid, "ticker not found", 0))
            continue
        n = len(b["pl"].get(cid, []))
        if n < MIN_YEARS:
            skipped.append((cid, f"fewer than {MIN_YEARS} years of data", n))
            continue
        made.append(make_tearsheet(cid, b, out_dir))
    os.makedirs("output", exist_ok=True)
    pd.DataFrame(skipped, columns=["company_id", "reason", "years_available"]).to_csv(
        os.path.join("output", "skipped_tearsheets.csv"), index=False)
    return made, skipped


if __name__ == "__main__":
    files, skips = run_batch(sys.argv[1:] or None)
    print(f"Tearsheets written: {len(files)} -> {OUT_DIR}")
    print(f"Skipped: {len(skips)} {[s[0] for s in skips]}")
