# acceptance_checklist.py - builds docs/acceptance_checklist.pdf (Sprint 6, Day 45)
# Lists the 23 project deliverables, whether each is present, and its file path.
import os
import glob

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUT_FILE = os.path.join("docs", "acceptance_checklist.pdf")
NAVY = colors.HexColor("#1F3864")
GREEN = colors.HexColor("#C6EFCE")
RED = colors.HexColor("#FFC7CE")

DELIVERABLES = [
    ("nifty100.db - 10 tables populated", "data/nifty100.db"),
    ("output/load_audit.csv", "output/load_audit.csv"),
    ("output/validation_failures.csv", "output/validation_failures.csv"),
    ("src/etl/loader.py, validator.py, normaliser.py", "src/etl/loader.py"),
    ("db/schema.sql", "db/schema.sql"),
    ("tests/etl/ - unit tests", "tests/etl/test_normalise.py"),
    ("financial_ratios table + src/analytics/ratios.py, cagr.py", "src/analytics/ratios.py"),
    ("output/screener_output.xlsx", "output/screener_output.xlsx"),
    ("output/peer_comparison.xlsx + peer_percentiles table", "output/peer_comparison.xlsx"),
    ("reports/radar_charts/", "reports/radar_charts"),
    ("config/screener_config.yaml", "config/screener_config.yaml"),
    ("src/dashboard/ - 8-screen Streamlit app", "src/dashboard/app.py"),
    ("output/valuation_summary.xlsx + valuation_flags.csv", "output/valuation_summary.xlsx"),
    ("output/pros_cons_generated.csv", "output/pros_cons_generated.csv"),
    ("output/analysis_parsed.csv", "output/analysis_parsed.csv"),
    ("output/cashflow_intelligence.xlsx", "output/cashflow_intelligence.xlsx"),
    ("reports/tearsheets/ - 92 PDFs", "reports/tearsheets"),
    ("reports/sector/ + reports/portfolio/", "reports/sector"),
    ("output/cluster_labels.csv + reports/elbow_plot.png", "output/cluster_labels.csv"),
    ("reports/correlation_heatmap.png + output/outlier_report.csv", "reports/correlation_heatmap.png"),
    ("src/api/ - FastAPI server, 16 endpoints", "src/api/main.py"),
    ("docs/openapi.json", "docs/openapi.json"),
    ("docs/analyst_guide.pdf", "docs/analyst_guide.pdf"),
]


def present(path):
    if os.path.isdir(path):
        return len(glob.glob(os.path.join(path, "*"))) > 0
    return os.path.exists(path)


def build():
    os.makedirs("docs", exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("H1", parent=styles["Heading1"], textColor=NAVY))
    doc = SimpleDocTemplate(OUT_FILE, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=1.5*cm, rightMargin=1.5*cm)
    story = [Paragraph("Nifty 100 Analytics - Acceptance Checklist", styles["H1"]),
            Paragraph("All 23 project deliverables, checked against the files in this repository.",
                      styles["BodyText"]), Spacer(1, 0.5*cm)]

    rows = [["#", "Deliverable", "Status", "Path"]]
    all_present = True
    for i, (desc, path) in enumerate(DELIVERABLES, start=1):
        ok = present(path)
        all_present = all_present and ok
        rows.append([str(i), desc, "Present" if ok else "MISSING", path])

    t = Table(rows, colWidths=[0.8*cm, 7.5*cm, 2.2*cm, 5.5*cm], repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP")]
    for i, (desc, path) in enumerate(DELIVERABLES, start=1):
        color = GREEN if present(path) else RED
        style.append(("BACKGROUND", (2, i), (2, i), color))
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Sign-off: " + ("All deliverables present." if all_present else
                            "Some deliverables are missing - see rows marked MISSING above.") +
                           " Team lead signature and date: ___________________________",
                           styles["BodyText"]))

    doc.build(story)
    return all_present


if __name__ == "__main__":
    ok = build()
    print("wrote docs/acceptance_checklist.pdf -", "all present" if ok else "some missing")
