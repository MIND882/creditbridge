"""
GSTN Service — wrapper around GSP for GSTIN verification
"""
from app.services.gsp_service import fetch_gstin_details, fetch_gstr3b
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def verify_and_fetch_gst(gstin: str) -> dict:
    """Combined: verify GSTIN + fetch returns"""
    details = await fetch_gstin_details(gstin)
    returns = await fetch_gstr3b(gstin, months=12)
    return {
        "verified":      details.get("status") == "Active",
        "details":       details,
        "returns":       returns,
        "gst_score":     _compute_gst_score(details, returns),
    }


def _compute_gst_score(details: dict, returns: dict) -> int:
    score = 0
    if details.get("status") == "Active":   score += 40
    if returns.get("compliance", 0) >= 80:  score += 30
    if returns.get("compliance", 0) >= 100: score += 10
    if returns.get("total_turnover", 0) > 0: score += 20
    return min(100, score)