# companies.py - company data endpoints (Sprint 6, Day 39)
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.api import db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def list_companies(
    sector: str = None, market_cap_category: str = None, search: str = None
):
    """List all companies, with optional filters on sector, market cap category or a name/ticker search."""
    ratios = db.latest_ratios()[
        ["company_id", "return_on_equity_pct", "return_on_capital_employed_pct"]
    ]
    companies = db.query_df(
        "SELECT c.id AS company_id, c.company_name, s.broad_sector, s.sub_sector, "
        "s.market_cap_category FROM companies c LEFT JOIN sectors s ON s.company_id = c.id"
    )
    df = companies.merge(ratios, on="company_id", how="left")
    df = df.rename(
        columns={
            "return_on_equity_pct": "roe_pct",
            "return_on_capital_employed_pct": "roce_pct",
        }
    )

    if sector:
        df = df[df["broad_sector"].str.lower() == sector.lower()]
    if market_cap_category:
        df = df[df["market_cap_category"].str.lower() == market_cap_category.lower()]
    if search:
        needle = search.lower()
        df = df[
            df["company_name"].str.lower().str.contains(needle, na=False)
            | df["company_id"].str.lower().str.contains(needle, na=False)
        ]

    return {"count": len(df), "results": df.pipe(db.clean_records)}


@router.get("/{ticker}")
def company_profile(ticker: str):
    """Full company profile: company info + latest year KPIs + sector data."""
    ticker = db.company_or_404(ticker)
    info = (
        db.query_df("SELECT * FROM companies WHERE id = ?", (ticker,)).iloc[0].to_dict()
    )
    sector = db.query_df("SELECT * FROM sectors WHERE company_id = ?", (ticker,))
    ratios = db.latest_ratios()
    latest = ratios[ratios["company_id"] == ticker]

    result = {k: (None if v != v else v) for k, v in info.items()}
    result["sector"] = sector.pipe(db.clean_records)[0] if len(sector) else None
    result["latest_ratios"] = latest.pipe(db.clean_records)[0] if len(latest) else None
    return result


def _year_filtered(table, ticker, from_year, to_year):
    sql = "SELECT * FROM " + table + " WHERE company_id = ?"
    params = [ticker]
    if from_year:
        sql += " AND year >= ?"
        params.append(from_year)
    if to_year:
        sql += " AND year <= ?"
        params.append(to_year)
    sql += " ORDER BY year"
    df = db.query_df(sql, tuple(params))
    return df.pipe(db.clean_records)


@router.get("/{ticker}/pl")
def profit_and_loss(ticker: str, from_year: str = None, to_year: str = None):
    """Profit and loss history. from_year/to_year are in YYYY-MM format."""
    ticker = db.company_or_404(ticker)
    return {
        "company_id": ticker,
        "history": _year_filtered("profitandloss", ticker, from_year, to_year),
    }


@router.get("/{ticker}/bs")
def balance_sheet(ticker: str, from_year: str = None, to_year: str = None):
    """Balance sheet history. from_year/to_year are in YYYY-MM format."""
    ticker = db.company_or_404(ticker)
    return {
        "company_id": ticker,
        "history": _year_filtered("balancesheet", ticker, from_year, to_year),
    }


@router.get("/{ticker}/cashflow")
def cash_flow(ticker: str, from_year: str = None, to_year: str = None):
    """Cash flow history. from_year/to_year are in YYYY-MM format."""
    ticker = db.company_or_404(ticker)
    return {
        "company_id": ticker,
        "history": _year_filtered("cashflow", ticker, from_year, to_year),
    }


@router.get("/{ticker}/ratios")
def ratios(ticker: str, year: str = None):
    """All computed KPIs per year for the company, or a single year if `year` is given."""
    ticker = db.company_or_404(ticker)
    df = db.query_df(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", (ticker,)
    )
    if year:
        df = df[df["year"] == year]
        if len(df) == 0:
            raise HTTPException(
                status_code=404, detail="No ratio data for %s in %s" % (ticker, year)
            )
    return {"company_id": ticker, "ratios": df.pipe(db.clean_records)}


@router.get("/{ticker}/tearsheet")
def tearsheet(ticker: str):
    """Download the pre-generated 2-page tearsheet PDF for this company."""
    ticker = db.company_or_404(ticker)
    path = os.path.join(db.REPORTS_DIR, "tearsheets", ticker + "_tearsheet.pdf")
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404, detail="Tearsheet not generated for " + ticker
        )
    return FileResponse(
        path, media_type="application/pdf", filename=ticker + "_tearsheet.pdf"
    )


@router.get("/{ticker}/peers/compare")
def peer_compare(ticker: str):
    """Radar data: this company's 8 axis metrics + the peer group average + the benchmark company."""
    ticker = db.company_or_404(ticker)
    group_row = db.query_df(
        "SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (ticker,)
    )
    if len(group_row) == 0:
        return {"company_id": ticker, "message": "No peer group assigned"}
    group = group_row.iloc[0]["peer_group_name"]

    members = db.query_df(
        "SELECT company_id, is_benchmark FROM peer_groups WHERE peer_group_name = ?",
        (group,),
    )
    ratios = db.latest_ratios()
    group_ratios = ratios[ratios["company_id"].isin(members["company_id"])]

    axes = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
    ]
    company_row = group_ratios[group_ratios["company_id"] == ticker]
    company_values = {
        a: (
            None
            if len(company_row) == 0 or company_row.iloc[0][a] != company_row.iloc[0][a]
            else float(company_row.iloc[0][a])
        )
        for a in axes
    }
    averages = {
        a: (
            None
            if group_ratios[a].dropna().empty
            else round(float(group_ratios[a].mean()), 2)
        )
        for a in axes
    }

    benchmark_ids = members[members["is_benchmark"] == 1]["company_id"].tolist()
    benchmark_row = group_ratios[group_ratios["company_id"].isin(benchmark_ids)]
    benchmark_values = None
    if len(benchmark_row) > 0:
        b = benchmark_row.iloc[0]
        benchmark_values = {
            "company_id": b["company_id"],
            **{a: (None if b[a] != b[a] else float(b[a])) for a in axes},
        }

    return {
        "company_id": ticker,
        "peer_group_name": group,
        "axes": axes,
        "company_values": company_values,
        "peer_group_average": averages,
        "benchmark": benchmark_values,
    }


@router.get("/{ticker}/documents")
def documents(ticker: str):
    """Annual report links for this company, each flagged with whether the URL still works."""
    ticker = db.company_or_404(ticker)
    df = db.query_df(
        "SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC", (ticker,)
    )
    records = df.pipe(db.clean_records)
    import requests

    for r in records:
        url = r.get("annual_report")
        valid = False
        if url:
            try:
                resp = requests.head(url, timeout=3, allow_redirects=True)
                valid = resp.status_code < 400
            except Exception:
                valid = False
        r["is_url_valid"] = valid
    return {"company_id": ticker, "documents": records}
