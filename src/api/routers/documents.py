# documents.py - placeholder router (the actual endpoint lives under /companies/{ticker}/documents,
# kept as its own module per the plan's routers/ layout)
from fastapi import APIRouter

router = APIRouter(tags=["documents"])
