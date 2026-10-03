# main.py - FastAPI application entry point (Sprint 6, Day 38)
#
# Run from the project root:   uvicorn src.api.main:app --port 8000
# Interactive docs:            http://localhost:8000/docs

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("api.requests")

app = FastAPI(
    title="Nifty 100 Analytics API",
    version="1.0.0",
    description="REST API for the Nifty 100 fundamental analysis project.",
)

# internal use only, so every origin is allowed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")


@app.on_event("startup")
def warm_caches():
    """Load the screener universe once at startup instead of on the first request."""
    screener.get_universe()


@app.get("/")
def root():
    return {"message": "Nifty 100 Analytics API. See /docs for the endpoint list."}
