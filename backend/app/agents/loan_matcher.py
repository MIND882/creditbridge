"""
Loan Matcher Agent
Matches MSME credit profile to best available lenders
"""
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

LENDER_CRITERIA = [
    {
        "name": "Lendingkart NBFC",
        "min_score": 650, "max_amount": 20000000, "min_amount": 100000,
        "rate": 13.5, "tenure_months": 12, "processing_fee": 1.0,
        "accepts_no_gstin": True,  "min_vintage_months": 12,
        "preferred_types": ["textile", "manufacturing", "trading"],
    },
    {
        "name": "Kotak Mahindra Bank",
        "min_score": 700, "max_amount": 50000000, "min_amount": 500000,
        "rate": 14.2, "tenure_months": 24, "processing_fee": 1.5,
        "accepts_no_gstin": False, "min_vintage_months": 24,
        "preferred_types": ["manufacturing", "services", "retail"],
    },
    {
        "name": "HDFC Bank Overdraft",
        "min_score": 720, "max_amount": 30000000, "min_amount": 200000,
        "rate": 15.0, "tenure_months": 0, "processing_fee": 1.0,
        "accepts_no_gstin": False, "min_vintage_months": 18,
        "preferred_types": ["all"],
    },
    {
        "name": "Flexi Loans",
        "min_score": 600, "max_amount": 10000000, "min_amount": 50000,
        "rate": 18.0, "tenure_months": 6, "processing_fee": 2.0,
        "accepts_no_gstin": True,  "min_vintage_months": 6,
        "preferred_types": ["all"],
    },
    {
        "name": "Axis Bank MSME",
        "min_score": 680, "max_amount": 25000000, "min_amount": 300000,
        "rate": 14.8, "tenure_months": 18, "processing_fee": 1.25,
        "accepts_no_gstin": False, "min_vintage_months": 18,
        "preferred_types": ["manufacturing", "export", "textile"],
    },
]


def match_lenders(
    credit_score: int,
    requested_amount: float,
    has_gstin: bool = True,
    business_type: str = "general",
    vintage_months: int = 24,
) -> list[dict]:
    """
    Match MSME to eligible lenders based on credit profile.
    Returns ranked list of loan offers.
    """
    matched = []

    for lender in LENDER_CRITERIA:
        # Score check
        if credit_score < lender["min_score"]:
            continue
        # Amount check
        if requested_amount < lender["min_amount"] or requested_amount > lender["max_amount"]:
            continue
        # GSTIN check
        if not has_gstin and not lender["accepts_no_gstin"]:
            continue
        # Vintage check
        if vintage_months < lender["min_vintage_months"]:
            continue

        # Compute match score
        score_margin  = credit_score - lender["min_score"]
        match_quality = min(100, 60 + (score_margin // 5))

        matched.append({
            "lender":          lender["name"],
            "amount":          min(requested_amount * 1.1, lender["max_amount"]),
            "rate":            lender["rate"],
            "tenure":          lender["tenure_months"],
            "processing_fee":  lender["processing_fee"],
            "match_quality":   match_quality,
            "featured":        match_quality >= 80,
        })

    # Sort by rate ascending (cheapest first)
    matched.sort(key=lambda x: x["rate"])

    # Mark best match
    if matched:
        matched[0]["featured"] = True

    logger.info(f"Matched {len(matched)} lenders for score={credit_score}, amount={requested_amount}")
    return matched


def get_recommended_amount(
    avg_monthly_revenue: float,
    credit_score: int,
) -> float:
    """Recommend loan amount based on revenue and score."""
    multiplier = 1.5 if credit_score >= 750 else 1.0 if credit_score >= 700 else 0.75
    recommended = avg_monthly_revenue * 3 * multiplier
    return min(recommended, 20000000)  # Cap at 2Cr