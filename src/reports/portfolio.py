# portfolio.py - portfolio summary PDF, one page per company, alphabetical (Sprint 5, Day 35)
#
# Run from the project root:   python -m src.reports.portfolio
# Writes reports/portfolio/portfolio_summary.pdf
#
# Arrows compare the latest year with the year before:
#   up (green)  = the metric got better       down (red) = it got worse
#   right (grey) = changed by 2% or less      dash       = no earlier year to compare
# For debt-to-equity LOWER is better, so a fall shows as an up arrow.

import os

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.reports.common import GREEN, GREY, LIGHT, NAVY, RED, esc, fmt, load_bundle

OUT_FILE = os.path.join("reports", "portfolio", "portfolio_summary.pdf")
MARGIN = 2 * cm
W = A4[0] - 2 * MARGIN
FLAT_PCT = 2.0
base = getSampleStyleSheet()
CELL = ParagraphStyle("c", parent=base["Normal"], fontSize=10, leading=13)
HEAD = ParagraphStyle("h", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")

# (column, label, suffix, decimals, higher_is_better)
KPIS = [("return_on_equity_pct", "ROE", "%", 1, True), ("return_on_capital_employed_pct", "ROCE", "%", 1, True),
        ("net_profit_margin_pct", "Net profit margin", "%", 1, True), ("debt_to_equity", "Debt to equity", "", 2, False),
        ("revenue_cagr_5yr", "Revenue CAGR 5yr", "%", 1, True), ("free_cash_flow_cr", "Free cash flow (Rs Cr)", "", 0, True)]


def trend(new, old, higher_is_better):
    # returns "up", "down", "flat" or None
    if pd.isna(new) or pd.isna(old):
        return None
    if old == 0:
        change = 0.0 if new == 0 else np.inf * np.sign(new)
    else:
        change = (new - old) / abs(old) * 100
    if abs(change) <= FLAT_PCT:
        return "flat"
    better = change > 0 if higher_is_better else change < 0
    return "up" if better else "down"


class Arrow(Flowable):
    # a small drawn arrow (the built-in PDF fonts have no arrow characters)
    def __init__(self, kind, size=14):
        super().__init__()
        self.kind, self.size = kind, size
        self.width = self.height = size

    def draw(self):
        c, s = self.canv, self.size
        if self.kind is None:
            c.setStrokeColor(GREY)
            c.line(s * 0.25, s / 2, s * 0.75, s / 2)
            return
        color = {"up": GREEN, "down": RED, "flat": GREY}[self.kind]
        c.setFillColor(color)
        p = c.beginPath()
        if self.kind == "up":
            pts = [(s / 2, s), (s, s * 0.35), (s * 0.65, s * 0.35), (s * 0.65, 0), (s * 0.35, 0), (s * 0.35, s * 0.35), (0, s * 0.35)]
        elif self.kind == "down":
            pts = [(s / 2, 0), (s, s * 0.65), (s * 0.65, s * 0.65), (s * 0.65, s), (s * 0.35, s), (s * 0.35, s * 0.65), (0, s * 0.65)]
        else:
            pts = [(s, s / 2), (s * 0.35, s), (s * 0.35, s * 0.65), (0, s * 0.65), (0, s * 0.35), (s * 0.35, s * 0.35), (s * 0.35, 0)]
        p.moveTo(*pts[0])
        for pt in pts[1:]:
            p.lineTo(*pt)
        p.close()
        c.drawPath(p, fill=1, stroke=0)


def company_page(cid, b):
    info = b["companies"].loc[cid]
    r = b["ratios"].get(cid)
    r = r if r is not None else pd.DataFrame({"fy": []})
    last = r.iloc[-1] if len(r) else None
    prev = r.iloc[-2] if len(r) > 1 else None

    t1 = ParagraphStyle("t1", parent=base["Normal"], fontSize=20, leading=25, textColor=colors.white, fontName="Helvetica-Bold")
    t2 = ParagraphStyle("t2", parent=base["Normal"], fontSize=10, leading=14, textColor=colors.white)
    head = Table([[Paragraph(esc(info["company_name"]), t1)],
                  [Paragraph(f'{esc(cid)}  |  {esc(info["sector"] or "N/A")}  |  '
                             f'FY{int(last["fy"]) if last is not None else "N/A"}', t2)]], colWidths=[W])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                              ("TOPPADDING", (0, 0), (-1, 0), 12), ("BOTTOMPADDING", (0, -1), (-1, -1), 12)]))

    rows = [[Paragraph("KPI", HEAD), Paragraph("Latest", HEAD), Paragraph("Trend", HEAD), Paragraph("Previous year", HEAD)]]
    for col, label, suffix, dec, hib in KPIS:
        new = last[col] if last is not None else np.nan
        old = prev[col] if prev is not None else np.nan
        rows.append([Paragraph(esc(label), CELL), Paragraph(f"<b>{fmt(new, suffix, dec)}</b>", CELL),
                     Arrow(trend(new, old, hib)), Paragraph(fmt(old, suffix, dec), CELL)])
    t = Table(rows, colWidths=[W * 0.4, W * 0.22, W * 0.14, W * 0.24], rowHeights=[0.9 * cm] + [1.3 * cm] * len(KPIS))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey)]))
    legend = Paragraph("Arrows compare the latest year with the year before: green up = better, red down = worse, "
                       "grey right = within 2%. For debt to equity, lower is better. A dash means no earlier year to compare. Stock prices and market cap / valuation multiples in this project are SIMULATED.",
                       ParagraphStyle("lg", parent=CELL, fontSize=8, leading=10, textColor=GREY))
    return [head, Spacer(1, 16), t, Spacer(1, 10), legend]


def build(out_file=OUT_FILE):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    b = load_bundle()
    story = []
    for i, cid in enumerate(sorted(b["companies"].index)):
        if i:
            story.append(PageBreak())
        story += company_page(cid, b)
    SimpleDocTemplate(out_file, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                      bottomMargin=MARGIN, title="Nifty 100 portfolio summary").build(story)
    return out_file, len(b["companies"])


if __name__ == "__main__":
    path, n = build()
    print(f"Portfolio summary written: {path} ({n} pages expected)")
