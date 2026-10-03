# analyst_guide.py - builds docs/analyst_guide.pdf (Sprint 6, Day 44)
# Run from the project root:   python -m src.reports.analyst_guide
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_FILE = os.path.join("docs", "analyst_guide.pdf")
NAVY = colors.HexColor("#1F3864")

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle("H1", parent=styles["Heading1"], textColor=NAVY, spaceAfter=14)
)
styles.add(
    ParagraphStyle(
        "H2", parent=styles["Heading2"], textColor=NAVY, spaceBefore=10, spaceAfter=8
    )
)
styles.add(ParagraphStyle("Body", parent=styles["BodyText"], spaceAfter=8, leading=15))
styles.add(
    ParagraphStyle(
        "CodeBlock",
        parent=styles["Code"],
        backColor=colors.HexColor("#F2F2F2"),
        borderPadding=6,
        spaceAfter=10,
    )
)


def p(text, style="Body"):
    return Paragraph(text, styles[style])


def code(text):
    return Paragraph(text.replace("\n", "<br/>"), styles["CodeBlock"])


def bullets(items):
    return ListFlowable(
        [ListItem(p(i)) for i in items], bulletType="bullet", leftIndent=16
    )


def build():
    os.makedirs("docs", exist_ok=True)
    doc = SimpleDocTemplate(
        OUT_FILE,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    story = []

    # ---- cover ----
    story.append(Spacer(1, 5 * cm))
    story.append(
        Paragraph(
            "Nifty 100 Analytics",
            ParagraphStyle(
                "Title", parent=styles["Title"], fontSize=28, textColor=NAVY
            ),
        )
    )
    story.append(p("Analyst Guide", "H2"))
    story.append(Spacer(1, 1 * cm))
    story.append(p("Covers the Streamlit dashboard, PDF tearsheets, and the REST API."))
    story.append(PageBreak())

    # ---- table of contents ----
    story.append(p("Contents", "H1"))
    toc = [
        "1. Getting started",
        "2. The Streamlit dashboard - screen by screen",
        "3. Using the screener",
        "4. Generating PDF tearsheets",
        "5. Calling the API",
        "6. Troubleshooting common issues",
    ]
    story.append(bullets(toc))
    story.append(PageBreak())

    # ---- 1. getting started ----
    story.append(p("1. Getting started", "H1"))
    story.append(p("Set up the project once:"))
    story.append(
        code(
            "python -m venv .venv\n.venv\\Scripts\\activate      (Mac/Linux: source .venv/bin/activate)\n"
            "pip install -r requirements.txt"
        )
    )
    story.append(p("Rebuild the database and every downstream file, in order:"))
    story.append(
        code(
            "python src/etl/loader.py\npython -m src.analytics.run_ratio_engine\n"
            "python -m src.screener.run_screener\npython -m src.analytics.peer\n"
            "python -m src.analytics.peer_report\npython -m src.analytics.valuation\n"
            "python -m src.analytics.clustering"
        )
    )
    story.append(PageBreak())

    # ---- 2. dashboard screens ----
    story.append(p("2. The Streamlit dashboard - screen by screen", "H1"))
    story.append(p("Start the dashboard with:"))
    story.append(code("streamlit run src/dashboard/app.py"))
    story.append(
        p("It opens at http://localhost:8501. The sidebar lists all 8 screens:")
    )
    rows = [
        ["#", "Screen", "What it's for"],
        ["1", "Home", "6 KPI tiles, sector donut chart, top 5 companies by score."],
        [
            "2",
            "Company Profile",
            "Search a ticker; see its KPIs, 10-year charts, pros and cons.",
        ],
        [
            "3",
            "Screener",
            "Filter the universe with sliders or the 6 presets; export to CSV.",
        ],
        [
            "4",
            "Peer Comparison",
            "Radar chart and side-by-side table for a peer group.",
        ],
        [
            "5",
            "Trend Analysis",
            "Overlay up to 3 metrics over 10 years, with YoY change.",
        ],
        [
            "6",
            "Sector Analysis",
            "Bubble chart (revenue vs ROE) and sector median KPIs.",
        ],
        ["7", "Capital Allocation", "Treemap of the 8 capital allocation patterns."],
        ["8", "Annual Reports", "Links to each company's annual reports by year."],
    ]
    t = Table(rows, colWidths=[1.2 * cm, 3.5 * cm, 10.3 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7F7F7")],
                ),
            ]
        )
    )
    story.append(t)
    story.append(PageBreak())

    # ---- 3. screener ----
    story.append(p("3. Using the screener", "H1"))
    story.append(p("The Screener screen (page 3) has two ways to filter companies:"))
    story.append(
        bullets(
            [
                "<b>Presets</b> - click one of the 6 buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround) "
                "to auto-fill the sliders with that preset's thresholds.",
                "<b>Manual sliders</b> - 10 sliders in the sidebar for ROE, D/E, FCF, Revenue CAGR, PAT CAGR, OPM, "
                "P/E, P/B, Dividend Yield and Interest Coverage. Move any slider to change the result table live.",
            ]
        )
    )
    story.append(
        p(
            'The result count is shown above the table (for example, "23 companies match your '
            'filters"). Click <b>Download CSV</b> to export the visible columns.'
        )
    )
    story.append(
        p(
            "Banks and other Financials-sector companies are excluded from the D/E filter, because "
            'high leverage is normal for them. A "Debt Free" company always passes any minimum '
            "interest coverage filter."
        )
    )
    story.append(PageBreak())

    # ---- 4. tearsheets ----
    story.append(p("4. Generating PDF tearsheets", "H1"))
    story.append(
        p(
            "Every company has a 2-page tearsheet PDF in reports/tearsheets/. To regenerate all "
            "of them (for example after a fresh data load):"
        )
    )
    story.append(code("python -m src.reports.tearsheet"))
    story.append(
        p(
            "Companies with no profit and loss data are skipped, and logged to "
            "output/skipped_tearsheets.csv. Companies with fewer than 3 years of data (for example JIOFIN) "
            "still get a tearsheet that carries a limited-history note. To regenerate the 11 sector PDFs and the portfolio "
            "summary PDF:"
        )
    )
    story.append(
        code("python -m src.reports.sector_report\npython -m src.reports.portfolio")
    )
    story.append(
        p("You can also download a single tearsheet from the API - see section 5.")
    )
    story.append(PageBreak())

    # ---- 5. API ----
    story.append(p("5. Calling the API", "H1"))
    story.append(p("Start the API server:"))
    story.append(code("uvicorn src.api.main:app --port 8000"))
    story.append(
        p(
            "Interactive documentation (try every endpoint from the browser) is at "
            "http://localhost:8000/docs. All endpoints are under /api/v1. Some examples:"
        )
    )
    story.append(
        code(
            "curl http://localhost:8000/api/v1/health\n\n"
            "curl http://localhost:8000/api/v1/companies/TCS\n\n"
            'curl "http://localhost:8000/api/v1/screener?min_roe=15&max_de=1"\n\n'
            "curl http://localhost:8000/api/v1/sectors\n\n"
            'curl "http://localhost:8000/api/v1/peers/IT%20Services"\n\n'
            "curl -o tcs_tearsheet.pdf http://localhost:8000/api/v1/companies/TCS/tearsheet"
        )
    )
    story.append(
        p(
            "The full list of endpoints and their parameters is in docs/openapi.json, and can "
            "also be imported into Postman from docs/postman_collection.json."
        )
    )
    story.append(PageBreak())

    # ---- 6. troubleshooting ----
    story.append(p("6. Troubleshooting common issues", "H1"))
    rows = [
        ["Problem", "Likely cause / fix"],
        [
            "\"ModuleNotFoundError: No module named 'src'\"",
            "You are not in the project root. cd into "
            "the folder that contains src/, data/ and tests/, then try again.",
        ],
        [
            "\"ModuleNotFoundError: No module named 'pandas'\" (or similar)",
            "Your virtual environment "
            "is not active, or the libraries were never installed. Run pip install -r requirements.txt.",
        ],
        [
            'Streamlit says "no such table"',
            "The database is empty or out of date. Run "
            "python src/etl/loader.py, then python -m src.analytics.run_ratio_engine.",
        ],
        [
            'A ticker shows "Ticker not found" on the Profile screen',
            "Check the spelling against "
            "the Home screen's company list - tickers use the NSE symbol, e.g. M&M not MAHINDRA.",
        ],
        [
            "The API returns HTTP 404 for a company",
            "The ticker must be uppercase and match the id "
            "column in the companies table exactly.",
        ],
        [
            "The API returns HTTP 400 on the screener",
            "One of the numeric query parameters "
            "(min_roe, max_de, ...) is not a valid number.",
        ],
        [
            "A tearsheet download 404s",
            "That company has no profit and loss data and was skipped - "
            "check output/skipped_tearsheets.csv.",
        ],
        [
            "Streamlit and the API both need to run at the same time",
            "Use two terminals: one running "
            "streamlit run src/dashboard/app.py, the other uvicorn src.api.main:app --port 8000. They "
            "use different ports (8501 and 8000) and do not conflict.",
        ],
    ]
    t = Table(rows, colWidths=[6.5 * cm, 8.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7F7F7")],
                ),
            ]
        )
    )
    story.append(t)
    story.append(PageBreak())

    # ---- 7. data notes ----
    story.append(p("7. Data notes and known limitations", "H1"))
    story.append(
        p("A few things worth knowing before presenting numbers from this project:")
    )
    story.append(
        bullets(
            [
                "The database holds 10 broad sectors. The 11th sector report, Conglomerates / Other, is a "
                "cross-cutting group of conglomerate, holding-company and diversified businesses, whose "
                "companies also appear in their own broad-sector reports.",
                "Market data (stock prices, market cap, P/E, P/B, dividend yield) is SIMULATED for this project and should not be "
                "used for real trading or investment decisions.",
                "A handful of companies (for example BEL, HAL, INDIGO) show return-on-equity figures above "
                "100% because of small or negative equity bases in the source data. These are flagged in "
                "output/outlier_report.csv and are capped (winsorised) in the composite quality score so "
                "they cannot dominate the screener rankings.",
                "'Debt Free' companies (no interest expense) are treated as having infinite interest "
                "coverage everywhere in the project - the screener, the API, and the pros/cons generator.",
            ]
        )
    )
    story.append(p("8. Where each report file comes from", "H2"))
    rows = [
        ["File", "Generated by"],
        ["output/screener_output.xlsx", "python -m src.screener.run_screener"],
        ["output/peer_comparison.xlsx", "python -m src.analytics.peer_report"],
        ["output/valuation_summary.xlsx", "python -m src.analytics.valuation"],
        ["output/cluster_labels.csv", "python -m src.analytics.clustering"],
        ["output/pros_cons_generated.csv", "python -m src.nlp.pros_cons_generator"],
        ["reports/tearsheets/*.pdf", "python -m src.reports.tearsheet"],
        [
            "docs/openapi.json",
            "generated from the running FastAPI app (src/api/main.py)",
        ],
    ]
    t2 = Table(rows, colWidths=[7 * cm, 8 * cm])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t2)
    story.append(PageBreak())

    story.append(p("9. Glossary", "H1"))
    glossary = [
        (
            "ROE",
            "Return on Equity - net profit as a percentage of shareholder equity plus reserves.",
        ),
        (
            "ROCE",
            "Return on Capital Employed - EBIT as a percentage of equity, reserves and borrowings.",
        ),
        (
            "D/E",
            "Debt-to-Equity - total borrowings divided by equity plus reserves. 0 means no debt.",
        ),
        (
            "CAGR",
            "Compound Annual Growth Rate - the smoothed yearly growth rate over a period.",
        ),
        ("FCF", "Free Cash Flow - cash from operations plus cash used in investing."),
        (
            "ICR",
            "Interest Coverage Ratio - operating profit and other income divided by interest cost.",
        ),
        ("OPM", "Operating Profit Margin - operating profit as a percentage of sales."),
        (
            "P/E, P/B",
            "Price-to-Earnings and Price-to-Book - valuation multiples from market price.",
        ),
        (
            "Composite score",
            "A 0-100 score combining profitability, cash quality, growth and leverage.",
        ),
    ]
    rows = [["Term", "Meaning"]] + [[a, b] for a, b in glossary]
    t3 = Table(rows, colWidths=[3 * cm, 12 * cm])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7F7F7")],
                ),
            ]
        )
    )
    story.append(t3)

    doc.build(story)
    return OUT_FILE


if __name__ == "__main__":
    path = build()
    import subprocess

    n = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    pages = [l for l in n.splitlines() if l.startswith("Pages")]
    print("wrote", path, "-", pages[0] if pages else "")
