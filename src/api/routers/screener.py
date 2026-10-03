# screener.py - GET /api/v1/screener (Sprint 6, Day 40)
from fastapi import APIRouter, HTTPException

from src.api import db
from src.screener import engine as E

router = APIRouter(tags=["screener"])

_universe_cache = {"df": None}

# query parameter name -> screener filter name
PARAMS = {
    "min_roe": "roe_min",
    "max_de": "de_max",
    "min_fcf": "fcf_min",
    "min_rev_cagr_5yr": "revenue_cagr_5yr_min",
    "min_pat_cagr_5yr": "pat_cagr_5yr_min",
    "max_pe": "pe_max",
}


def get_universe():
    if _universe_cache["df"] is None:
        _universe_cache["df"] = E.get_universe()
    return _universe_cache["df"]


def _to_float(name, raw):
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400, detail="Invalid value for %s: %r" % (name, raw)
        )


@router.get("/screener")
def screener(
    min_roe: str = None,
    max_de: str = None,
    min_fcf: str = None,
    sector: str = None,
    min_rev_cagr_5yr: str = None,
    min_pat_cagr_5yr: str = None,
    max_pe: str = None,
):
    """Filter the 92-company universe. All parameters are optional and combine with AND.
    Any non-numeric value for a numeric parameter returns HTTP 400."""
    raw = {
        "min_roe": min_roe,
        "max_de": max_de,
        "min_fcf": min_fcf,
        "min_rev_cagr_5yr": min_rev_cagr_5yr,
        "min_pat_cagr_5yr": min_pat_cagr_5yr,
        "max_pe": max_pe,
    }

    filters = {}
    for query_name, filter_name in PARAMS.items():
        value = raw[query_name]
        if value is not None:
            filters[filter_name] = _to_float(query_name, value)

    df = get_universe()
    result = E.apply_filters(df, filters) if filters else df
    if sector:
        result = result[result["broad_sector"].str.lower() == sector.lower()]

    cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "composite_quality_score",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "pe_ratio",
    ]
    out = db.clean_records(result[cols])
    return {"count": len(out), "results": out}
