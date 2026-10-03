# valuation.py - GET /api/v1/market-cap/{ticker} (Sprint 6, Day 40)
from fastapi import APIRouter

from src.api import db

router = APIRouter(tags=["valuation"])


@router.get("/market-cap/{ticker}")
def market_cap_history(ticker: str):
    """Historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield) from 2019 to 2024. Data is SIMULATED."""
    ticker = db.company_or_404(ticker)
    df = db.query_df(
        "SELECT * FROM market_cap WHERE company_id = ? AND year BETWEEN 2019 AND 2024 "
        "ORDER BY year",
        (ticker,),
    )
    return {"company_id": ticker, "data_label": "SIMULATED", "history": db.clean_records(df)}
