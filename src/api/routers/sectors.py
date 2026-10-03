# sectors.py - sector endpoints (Sprint 6, Day 40)
from fastapi import APIRouter, HTTPException

from src.api import db

router = APIRouter(prefix="/sectors", tags=["sectors"])


def _merged():
    ratios = db.latest_ratios()
    sectors = db.query_df("SELECT company_id, broad_sector FROM sectors")
    mc = db.query_df("SELECT company_id, pe_ratio FROM market_cap")
    mc = mc.sort_values("company_id").groupby("company_id").tail(1)
    return ratios.merge(sectors, on="company_id", how="left").merge(
        mc, on="company_id", how="left"
    )


@router.get("")
def list_sectors():
    """All broad sectors with company count and median ROE / P/E / D/E."""
    df = _merged()
    rows = []
    for sector, group in df.groupby("broad_sector"):
        rows.append(
            {
                "sector": sector,
                "company_count": len(group),
                "median_roe": (
                    None
                    if group["return_on_equity_pct"].dropna().empty
                    else round(float(group["return_on_equity_pct"].median()), 2)
                ),
                "median_pe": (
                    None
                    if group["pe_ratio"].dropna().empty
                    else round(float(group["pe_ratio"].median()), 2)
                ),
                "median_de": (
                    None
                    if group["debt_to_equity"].dropna().empty
                    else round(float(group["debt_to_equity"].median()), 2)
                ),
            }
        )
    return {"count": len(rows), "sectors": rows}


@router.get("/{sector}/companies")
def sector_companies(sector: str):
    """All companies in a sector with their latest year KPIs."""
    df = _merged()
    match = df[df["broad_sector"].str.lower() == sector.lower()]
    if len(match) == 0:
        raise HTTPException(status_code=404, detail="Unknown sector: " + sector)
    names = db.query_df("SELECT id AS company_id, company_name FROM companies")
    match = match.merge(names, on="company_id", how="left")
    return {
        "sector": sector,
        "count": len(match),
        "companies": match.pipe(db.clean_records),
    }
