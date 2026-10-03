# health.py - GET /api/v1/health (Sprint 6, Day 38)
from fastapi import APIRouter

from src.api import db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Basic liveness and status check for the API."""
    return {
        "status": "ok",
        "db_row_counts": db.table_row_counts(),
        "uptime_seconds": db.uptime_seconds(),
        "version": db.VERSION,
    }
