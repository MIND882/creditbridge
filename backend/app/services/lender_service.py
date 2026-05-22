"""
Lender Service
Manages lender API keys, feed updates, and portfolio alerts
"""
from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.risk_score import RiskScore
from app.models.loan_offer import LoanOffer
from app.utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

# Registered lenders (in production: DB table)
REGISTERED_LENDERS = {
    "lendingkart_2024": {
        "name": "Lendingkart NBFC", "tier": "premium",
        "min_score": 650, "webhook_url": None,
    },
    "kotak_msme_2024": {
        "name": "Kotak Mahindra Bank", "tier": "bank",
        "min_score": 700, "webhook_url": None,
    },
    "hdfc_msme_2024": {
        "name": "HDFC Bank", "tier": "bank",
        "min_score": 720, "webhook_url": None,
    },
}


def verify_lender_key(api_key: str) -> dict | None:
    """Verify lender API key — returns lender info or None"""
    return REGISTERED_LENDERS.get(api_key)


def get_msme_pool(db: Session, lender_key: str, min_score: int = 0) -> list:
    """
    Returns pre-underwritten MSME pool for lender
    Filtered by lender's minimum score requirement
    """
    lender = REGISTERED_LENDERS.get(lender_key, {})
    effective_min = max(min_score, lender.get("min_score", 0))

    businesses = db.query(Business).filter(Business.is_active == True).all()
    pool = []

    for biz in businesses:
        score_row = db.query(RiskScore).filter(
            RiskScore.business_id == biz.id
        ).order_by(RiskScore.created_at.desc()).first()

        if not score_row or score_row.score < effective_min:
            continue

        pool.append({
            "business_id":    str(biz.id),
            "business_name":  biz.business_name,
            "score":          score_row.score,
            "grade":          score_row.grade,
            "recommended_limit": float(score_row.recommended_limit or 0),
            "avg_monthly_revenue": float(score_row.avg_monthly_revenue or 0),
            "score_updated":  str(score_row.created_at)[:10],
            "loan_health":    _get_loan_health(score_row.score),
        })

    pool.sort(key=lambda x: x["score"], reverse=True)
    return pool


def get_portfolio_health(db: Session, lender_key: str) -> dict:
    """Active loan portfolio health for lender"""
    loans = db.query(LoanOffer).filter(
        LoanOffer.status == "accepted"
    ).all()

    total    = len(loans)
    stressed = 0
    green    = 0

    for loan in loans:
        score_row = db.query(RiskScore).filter(
            RiskScore.business_id == loan.business_id
        ).order_by(RiskScore.created_at.desc()).first()

        if score_row:
            if score_row.score >= 700: green    += 1
            elif score_row.score < 600: stressed += 1

    return {
        "total_active_loans":  total,
        "green":               green,
        "stressed":            stressed,
        "amber":               total - green - stressed,
        "npa_risk_count":      stressed,
        "portfolio_health":    "GREEN" if stressed == 0 else "AMBER" if stressed <= 2 else "RED",
    }


def _get_loan_health(score: int) -> str:
    if score >= 700: return "GREEN"
    if score >= 600: return "AMBER"
    return "RED"