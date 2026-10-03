# peer_report.py
# Writes output/peer_comparison.xlsx - one sheet for each peer group (Sprint 3, Day 20)
#
# Run from the project root (after python -m src.analytics.peer):
#   python -m src.analytics.peer_report

import os
import sqlite3

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from src.screener import engine as E
from src.analytics import peer as P

OUT_FILE = os.path.join("output", "peer_comparison.xlsx")

GREEN = PatternFill("solid", fgColor="C6EFCE")
YELLOW = PatternFill("solid", fgColor="FFEB9C")
RED = PatternFill("solid", fgColor="FFC7CE")
GOLD = PatternFill("solid", fgColor="FFD966")
HEADER = PatternFill("solid", fgColor="1F3864")
GREY = PatternFill("solid", fgColor="D9D9D9")


def percentile_fill(p):
    # p is on a 0-100 scale
    if p >= 75:
        return GREEN
    if p <= 25:
        return RED
    return YELLOW


def clean(value):
    if value is None or value != value:
        return None
    if isinstance(value, float):
        return round(value, 2)
    return value


def write_group_sheet(wb, group_name, members, universe, percentiles):
    ws = wb.create_sheet(group_name[:31])
    pct_columns = [m[0] for m in P.METRICS]
    headers = ["company_id", "company_name"] + E.KPI_COLUMNS + [c + " (pctile)" for c in pct_columns]

    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 48

    data = universe[universe["company_id"].isin(members["company_id"])]
    data = data.sort_values("composite_quality_score", ascending=False)
    benchmark_ids = set(members[members["is_benchmark"] == 1]["company_id"])

    # (company, metric) -> percentile on 0-100, for the company's latest year
    pct_lookup = {}
    for _, p in percentiles[percentiles["peer_group_name"] == group_name].iterrows():
        pct_lookup[(p["company_id"], p["metric"], p["year"])] = p["percentile_rank"] * 100

    r = 2
    first_data_row = r
    for _, row in data.iterrows():
        ws.cell(row=r, column=1, value=row["company_id"])
        ws.cell(row=r, column=2, value=row["company_name"])
        for c, column in enumerate(E.KPI_COLUMNS, start=3):
            if column == "interest_coverage" and row.get("icr_label") == "Debt Free":
                ws.cell(row=r, column=c, value="Debt Free")
            else:
                ws.cell(row=r, column=c, value=clean(row[column]))

        start = 3 + len(E.KPI_COLUMNS)
        for k, metric in enumerate(pct_columns):
            p = pct_lookup.get((row["company_id"], metric, int(row["fy"])))
            cell = ws.cell(row=r, column=start + k, value=None if p is None else round(p, 0))
            if p is not None:
                cell.fill = percentile_fill(p)

        if row["company_id"] in benchmark_ids:
            # gold background on the name columns and the KPI columns (percentile cells keep their colour)
            for c in range(1, start):
                ws.cell(row=r, column=c).fill = GOLD
            ws.cell(row=r, column=1).font = Font(bold=True)
        r += 1
    last_data_row = r - 1

    # summary row: median of each column for the group
    ws.cell(row=r, column=1, value="Peer group median").font = Font(bold=True)
    for c in range(1, len(headers) + 1):
        ws.cell(row=r, column=c).fill = GREY
    for c in range(3, len(headers) + 1):
        values = []
        for rr in range(first_data_row, last_data_row + 1):
            v = ws.cell(row=rr, column=c).value
            if isinstance(v, (int, float)):
                values.append(v)
        if values:
            median = pd.Series(values).median()
            ws.cell(row=r, column=c, value=round(float(median), 2)).font = Font(bold=True)

    ws.freeze_panes = "C2"
    for c in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 28 if c == 2 else 15


def main():
    conn = sqlite3.connect(E.DB_PATH)
    universe = E.load_universe(conn)
    groups = pd.read_sql("SELECT peer_group_name, company_id, is_benchmark FROM peer_groups", conn)
    percentiles = pd.read_sql("SELECT * FROM peer_percentiles", conn)
    conn.close()

    wb = Workbook()
    wb.remove(wb.active)
    for group_name in sorted(groups["peer_group_name"].unique()):
        members = groups[groups["peer_group_name"] == group_name]
        write_group_sheet(wb, group_name, members, universe, percentiles)

    os.makedirs("output", exist_ok=True)
    wb.save(OUT_FILE)
    print("peer_comparison.xlsx sheets:", len(wb.sheetnames), "->", OUT_FILE)


if __name__ == "__main__":
    main()
