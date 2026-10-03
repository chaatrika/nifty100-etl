# portfolio.py - GET /api/v1/portfolio/stats (Sprint 6, Day 40)
import os

from fastapi import APIRouter

from src.api import db

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/stats")
def portfolio_stats():
    """P10 through P90 percentile table for the 10 core KPIs across all 92 companies."""
    path = os.path.join(db.OUTPUT_DIR, "portfolio_stats.csv")
    if not os.path.exists(path):
        return {
            "message": "portfolio_stats.csv not generated yet - run python -m src.analytics.clustering"
        }
    import pandas as pd

    df = pd.read_csv(path)
    return {"metrics": df.to_dict("records")}
