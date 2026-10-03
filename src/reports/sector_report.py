# sector_report.py - one PDF per sector (Sprint 5, Day 34)
#
# Run from the project root:   python -m src.reports.sector_report
# Writes reports/sector/<Sector>_report.pdf  (page 1: median KPIs, then a table of every company with 8 metrics)

import os

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.reports.common import LIGHT, NAVY, esc, fmt, latest, load_bundle, safe_name

OUT_DIR = os.path.join("reports", "sector")
MARGIN = 1.5 * cm
W = A4[0] - 2 * MARGIN
base = getSampleStyleSheet()
CELL = ParagraphStyle("c", parent=base["Normal"], fontSize=7.5, leading=9)          # Paragraph cells = word wrap
HEAD = ParagraphStyle("hd", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")
NUM = ParagraphStyle("n", parent=CELL, alignment=2)
NUMHEAD = ParagraphStyle("nh", parent=HEAD, alignment=2)

# (column in the latest ratios row, header, suffix, decimals)
# The project spec lists 11 broad sectors; the 11th is "Conglomerates / Other". In the database these companies
# sit in other broad sectors, so this report is a cross-cutting group built from their sub-sector labels.
OTHER_GROUP = "Conglomerates / Other"
OTHER_KEYWORDS = ("conglomerate", "holding", "diversified")
METRICS = [("return_on_equity_pct", "ROE %", "", 1), ("return_on_capital_employed_pct", "ROCE %", "", 1),
           ("net_profit_margin_pct", "Net margin %", "", 1), ("debt_to_equity", "D/E", "", 2),
           ("revenue_cagr_5yr", "Rev CAGR 5yr %", "", 1), ("pat_cagr_5yr", "PAT CAGR 5yr %", "", 1),
           ("free_cash_flow_cr", "FCF (Rs Cr)", "", 0), ("pe_ratio", "P/E (SIMULATED)", "", 1)]


def group_members(b, sector):
    comp = b["companies"]
    if sector == OTHER_GROUP:
        sub = comp["sub_sector"].fillna("").str.lower()
        return comp[sub.apply(lambda s: any(k in s for k in OTHER_KEYWORDS))]
    return comp[comp["sector"] == sector]


def sector_frame(b, sector):
    rows = []
    for cid, info in group_members(b, sector).iterrows():
        r = b["ratios"].get(cid)
        mc = b["mc"].get(cid)
        row = {"company_id": cid, "company_name": info["company_name"]}
        for col, *_ in METRICS:
            row[col] = latest(mc, col) if col == "pe_ratio" else latest(r, col)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("company_id")


def make_sector_pdf(sector, b, out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    df = sector_frame(b, sector)
    path = os.path.join(out_dir, f"{safe_name(sector)}_report.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                            bottomMargin=MARGIN, title=f"{sector} sector report")

    t1 = ParagraphStyle("t1", parent=base["Normal"], fontSize=18, leading=23, textColor=colors.white, fontName="Helvetica-Bold")
    t2 = ParagraphStyle("t2", parent=base["Normal"], fontSize=9, leading=13, textColor=colors.white)
    title = Table([[Paragraph(esc(sector), t1)],
                   [Paragraph(f"Sector report | {len(df)} companies | latest year for each company", t2)]], colWidths=[W])
    title.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                               ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, -1), (-1, -1), 8)]))

    # sector summary: median of each KPI
    med = [[Paragraph("Median KPI", HEAD), Paragraph("Value", NUMHEAD), Paragraph("Companies with data", NUMHEAD)]]
    for col, head, suffix, dec in METRICS:
        med.append([Paragraph(esc(head), CELL), Paragraph(fmt(df[col].median(), suffix, dec), NUM),
                    Paragraph(str(int(df[col].notna().sum())), NUM)])
    mt = Table(med, colWidths=[W * 0.5, W * 0.25, W * 0.25], repeatRows=1)
    mt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey)]))

    # company table: 8 metrics per company
    widths = [W * 0.17, W * 0.12] + [W * 0.0825] * 7 + [W * 0.1325]
    head_row = [Paragraph("Company", HEAD), Paragraph("Ticker", HEAD)] + [Paragraph(esc(h), NUMHEAD) for _, h, *_ in METRICS]
    body = [[Paragraph(esc(r.company_name), CELL), Paragraph(esc(r.company_id), CELL)] +
            [Paragraph(fmt(getattr(r, col), suffix, dec), NUM) for col, _, suffix, dec in METRICS] for r in df.itertuples()]
    ct = Table([head_row] + body, colWidths=widths, repeatRows=1)
    ct.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))

    extra = (" This group spans companies whose sub-sector is a conglomerate, holding company or diversified business; "
             "they also appear in their own broad-sector reports.") if sector == OTHER_GROUP else ""
    note = Paragraph("D/E is not comparable for banks, insurers and NBFCs. N/A = no data. P/E is from the market cap table, which is SIMULATED data (not real market values)." + extra,
                     ParagraphStyle("nt", parent=CELL, textColor=colors.grey))
    story = [title, Spacer(1, 10), Paragraph("Sector summary", base["Heading3"]), mt, Spacer(1, 6), note,
             Spacer(1, 12), Paragraph("Companies in this sector", base["Heading3"]), ct]
    doc.build(story)
    return path


def run_batch(out_dir=OUT_DIR):
    b = load_bundle()
    sectors = sorted(b["companies"]["sector"].dropna().unique()) + [OTHER_GROUP]
    return [make_sector_pdf(s, b, out_dir) for s in sectors]


if __name__ == "__main__":
    files = run_batch()
    print(f"Sector reports written: {len(files)} -> {OUT_DIR}")
