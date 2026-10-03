# peers.py - GET /api/v1/peers/{group_name} (Sprint 6, Day 40)
from fastapi import APIRouter, HTTPException

from src.api import db

router = APIRouter(prefix="/peers", tags=["peers"])


@router.get("/{group_name}")
def peer_group(group_name: str):
    """All companies in a peer group with their percentile rank for each of the 10 metrics."""
    members = db.query_df(
        "SELECT company_id, is_benchmark FROM peer_groups WHERE peer_group_name = ?",
        (group_name,),
    )
    if len(members) == 0:
        raise HTTPException(status_code=404, detail="Unknown peer group: " + group_name)

    percentiles = db.query_df(
        "SELECT * FROM peer_percentiles WHERE peer_group_name = ?", (group_name,)
    )
    latest_year = percentiles["year"].max() if len(percentiles) else None
    percentiles = percentiles[percentiles["year"] == latest_year]

    names = db.query_df("SELECT id AS company_id, company_name FROM companies")
    companies = []
    for _, m in members.iterrows():
        rows = percentiles[percentiles["company_id"] == m["company_id"]]
        metrics = {
            r["metric"]: round(float(r["percentile_rank"]) * 100, 1)
            for _, r in rows.iterrows()
        }
        name = names[names["company_id"] == m["company_id"]]
        companies.append(
            {
                "company_id": m["company_id"],
                "company_name": name.iloc[0]["company_name"] if len(name) else None,
                "is_benchmark": bool(m["is_benchmark"]),
                "percentiles": metrics,
            }
        )
    return {
        "peer_group_name": group_name,
        "year": None if latest_year is None else int(latest_year),
        "count": len(companies),
        "companies": companies,
    }
