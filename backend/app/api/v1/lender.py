from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.loan_offer import Lender, LoanOffer
from app.models.risk_score import RiskScore
from app.models.business import Business
from app.models.rejection import Rejection as RejectionLog
from app.models.audit import AuditLog
from app.utils.logger import get_logger
from datetime import datetime
from uuid import UUID
import uuid
import secrets

router = APIRouter()
logger = get_logger(__name__)


# ─── Audit Helper ─────────────────────────────────────────────────

def log_audit(
    db: Session,
    lender_id,
    business_id=None,
    action: str = "",
    endpoint: str = ""
):
    """Log every lender action — mandatory for RBI compliance."""
    log = AuditLog(
        lender_id=lender_id,
        business_id=business_id,
        action=action,
        endpoint=endpoint
    )
    db.add(log)
    db.commit()


# ─── Lender Authentication ────────────────────────────────────────

def get_lender(
    x_api_key: str = Header(..., description="Lender API Key"),
    db: Session = Depends(get_db)
) -> Lender:
    """Dependency — validates lender API key on every request."""
    lender = db.query(Lender).filter(
        Lender.api_key == x_api_key,
        Lender.is_active == True
    ).first()
    if not lender:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return lender


# ─── Lender Registration ──────────────────────────────────────────

class LenderRegister(BaseModel):
    name: str
    type: str = "nbfc"
    contact_email: str
    contact_name: str
    min_score: int = 650
    min_monthly_turnover: float = 500000
    max_loan_amount: float = 10000000
    interest_rate_min: float = 12.0
    interest_rate_max: float = 18.0


@router.post("/register")
def register_lender(payload: LenderRegister, db: Session = Depends(get_db)):
    """Register a new lender — generates API key."""
    api_key = f"cb_live_{secrets.token_urlsafe(32)}"

    lender = Lender(
        name=payload.name,
        type=payload.type,
        contact_email=payload.contact_email,
        contact_name=payload.contact_name,
        api_key=api_key,
        min_score=payload.min_score,
        min_monthly_turnover=payload.min_monthly_turnover,
        max_loan_amount=payload.max_loan_amount,
        interest_rate_min=payload.interest_rate_min,
        interest_rate_max=payload.interest_rate_max,
        is_active=True
    )
    db.add(lender)
    db.commit()
    db.refresh(lender)

    logger.info(f"Lender registered: {lender.name}")

    return {
        "lender_id": str(lender.id),
        "name": lender.name,
        "api_key": api_key,
        "message": "Save this API key — it will not be shown again"
    }


# ─── MSME Pool View ───────────────────────────────────────────────

@router.get("/pool")
def get_msme_pool(
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    city: Optional[str] = None,
    business_type: Optional[str] = None,
    grade: Optional[str] = None,
    min_gst_score: Optional[int] = None,
    max_overdue_pct: Optional[float] = None,
    min_revenue: Optional[float] = None,
    limit: int = 50,
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """View MSME pool — filtered by risk segments."""

    query = db.query(RiskScore, Business).join(
        Business, RiskScore.business_id == Business.id
    ).filter(
        RiskScore.score >= (min_score or lender.min_score or 0)
    )

    if max_score:
        query = query.filter(RiskScore.score <= max_score)
    if city:
        query = query.filter(Business.city.ilike(f"%{city}%"))
    if business_type:
        query = query.filter(Business.business_type == business_type)
    if grade:
        query = query.filter(RiskScore.grade == grade)
    if min_gst_score:
        query = query.filter(RiskScore.gst_compliance_score >= min_gst_score)

    results = query.order_by(RiskScore.score.desc()).limit(limit).all()

    pool = []
    for score, business in results:
        flags = score.flags or []
        has_overdue = "high_overdue" in flags
        if max_overdue_pct is not None and has_overdue:
            continue

        pool.append({
            "business_id": str(business.id),
            "business_name": business.business_name,
            "city": business.city,
            "business_type": business.business_type,
            "score": score.score,
            "grade": score.grade,
            "recommended_limit": float(score.recommended_limit or 0),
            "cash_flow_score": score.cash_flow_score,
            "payment_discipline_score": score.payment_discipline_score,
            "gst_compliance_score": score.gst_compliance_score,
            "confidence": float(score.confidence or 0),
            "flags": flags,
            "positive_factors": score.positive_factors or [],
            "data_months": score.data_months,
            "computed_at": str(score.computed_at)
        })

    # ✅ Audit log — lender viewed MSME pool
    log_audit(
        db, lender.id,
        action="viewed_pool",
        endpoint="/v1/lender/pool"
    )

    return {
        "lender": lender.name,
        "total_in_pool": len(pool),
        "filters_applied": {
            "min_score": min_score or lender.min_score,
            "min_gst_score": min_gst_score,
            "city": city,
            "business_type": business_type,
            "grade": grade
        },
        "pool": pool
    }


# ─── Risk Segments Overview ───────────────────────────────────────

@router.get("/segments")
def get_risk_segments(
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """Portfolio risk segmentation."""
    all_scores = db.query(RiskScore).all()

    segments = {
        "A+": {"grade": "A+", "range": "800-900", "count": 0, "avg_limit": 0, "total_limit": 0},
        "A":  {"grade": "A",  "range": "750-799", "count": 0, "avg_limit": 0, "total_limit": 0},
        "B+": {"grade": "B+", "range": "700-749", "count": 0, "avg_limit": 0, "total_limit": 0},
        "B":  {"grade": "B",  "range": "650-699", "count": 0, "avg_limit": 0, "total_limit": 0},
        "C+": {"grade": "C+", "range": "600-649", "count": 0, "avg_limit": 0, "total_limit": 0},
        "C":  {"grade": "C",  "range": "300-599", "count": 0, "avg_limit": 0, "total_limit": 0},
    }

    total_deployable = 0
    for score in all_scores:
        grade = score.grade or "C"
        if grade in segments:
            segments[grade]["count"] += 1
            limit = float(score.recommended_limit or 0)
            segments[grade]["total_limit"] += limit
            total_deployable += limit

    for grade, seg in segments.items():
        if seg["count"] > 0:
            seg["avg_limit"] = seg["total_limit"] / seg["count"]

    # ✅ Audit log — lender viewed risk segments
    log_audit(
        db, lender.id,
        action="viewed_segments",
        endpoint="/v1/lender/segments"
    )

    return {
        "lender": lender.name,
        "total_businesses": len(all_scores),
        "total_deployable_capital": total_deployable,
        "segments": list(segments.values()),
        "recommendation": _get_portfolio_recommendation(segments)
    }


def _get_portfolio_recommendation(segments: dict) -> str:
    a_plus = segments["A+"]["count"]
    a = segments["A"]["count"]
    total = sum(s["count"] for s in segments.values())

    if total == 0:
        return "No businesses in pool yet."

    premium_pct = (a_plus + a) / total * 100
    if premium_pct >= 60:
        return f"{premium_pct:.0f}% businesses are A/A+ grade — excellent pool quality for low-NPA lending."
    elif premium_pct >= 40:
        return f"{premium_pct:.0f}% businesses are A/A+ grade — good pool. Consider B+ segment for volume."
    else:
        return "Pool has significant B/C segment. Risk-based pricing recommended."


# ─── Individual Business Deep Dive ───────────────────────────────

@router.get("/business/{business_id}")
def get_business_detail(
    business_id: str,
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """Full risk detail for a specific business — for underwriting."""
    bid = UUID(business_id)

    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    score = db.query(RiskScore).filter(RiskScore.business_id == bid).first()
    if not score:
        raise HTTPException(status_code=404, detail="No risk score available")

    rejections = db.query(RejectionLog).filter(
    RejectionLog.business_id == bid
    ).all()
    recommendation = _get_approval_recommendation(score, lender)

    # ✅ Audit log — lender viewed specific business detail
    log_audit(
        db, lender.id,
        business_id=str(bid),
        action="viewed_business_detail",
        endpoint=f"/v1/lender/business/{business_id}"
    )

    return {
        "business": {
            "id": str(business.id),
            "name": business.business_name,
            "owner": business.owner_name,
            "city": business.city,
            "type": business.business_type,
            "gstin": business.gstin
        },
        "risk_profile": {
            "score": score.score,
            "grade": score.grade,
            "cash_flow_score": score.cash_flow_score,
            "payment_discipline_score": score.payment_discipline_score,
            "gst_compliance_score": score.gst_compliance_score,
            "revenue_growth_score": score.revenue_growth_score,
            "recommended_limit": float(score.recommended_limit or 0),
            "recommended_tenure_months": score.recommended_tenure_months,
            "flags": score.flags or [],
            "positive_factors": score.positive_factors or [],
            "improvement_areas": score.improvement_areas or [],
            "confidence": float(score.confidence or 0),
            "data_months": score.data_months
        },
        "underwriting_recommendation": recommendation,
        "past_rejections": len(rejections),
        "raw_signals": score.raw_signals
    }


def _get_approval_recommendation(score: RiskScore, lender: Lender) -> dict:
    min_score = lender.min_score or 650

    if score.score >= 800:
        return {
            "decision": "APPROVE",
            "confidence": "HIGH",
            "suggested_amount": float(score.recommended_limit or 0),
            "suggested_rate": float(lender.interest_rate_min or 13.5),
            "reason": "Excellent credit profile. A+ grade with strong payment discipline."
        }
    elif score.score >= 700:
        return {
            "decision": "APPROVE",
            "confidence": "MEDIUM",
            "suggested_amount": float(score.recommended_limit or 0) * 0.8,
            "suggested_rate": float(lender.interest_rate_min or 13.5) + 1.5,
            "reason": "Good credit profile. Standard terms recommended."
        }
    elif score.score >= min_score:
        return {
            "decision": "CONDITIONAL",
            "confidence": "LOW",
            "suggested_amount": float(score.recommended_limit or 0) * 0.6,
            "suggested_rate": float(lender.interest_rate_max or 18.0),
            "reason": "Borderline profile. Additional collateral or guarantor recommended."
        }
    else:
        return {
            "decision": "REJECT",
            "confidence": "HIGH",
            "suggested_amount": 0,
            "suggested_rate": 0,
            "reason": f"Score {score.score} below minimum threshold {min_score}."
        }


# ─── Score Explainability ─────────────────────────────────────────

@router.get("/explain/{business_id}")
def explain_score(
    business_id: str,
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """WHY did this business get this score? Critical for lender trust."""
    bid = UUID(business_id)

    score = db.query(RiskScore).filter(RiskScore.business_id == bid).first()
    if not score:
        raise HTTPException(status_code=404, detail="No score found")

    signals = score.raw_signals or {}

    # ✅ Audit log — lender requested score explanation
    log_audit(
        db, lender.id,
        business_id=str(bid),
        action="viewed_score_explanation",
        endpoint=f"/v1/lender/explain/{business_id}"
    )

    return {
        "score": score.score,
        "grade": score.grade,
        "breakdown": [
            {
                "factor": "Cash Flow Strength",
                "score": score.cash_flow_score,
                "weight": "35%",
                "contribution": round((score.cash_flow_score or 0) * 0.35, 1),
                "explanation": f"Monthly revenue ₹{signals.get('avg_monthly_revenue', 0) / 100000:.1f}L — "
                               f"{'strong' if (score.cash_flow_score or 0) >= 80 else 'moderate' if (score.cash_flow_score or 0) >= 60 else 'weak'}"
            },
            {
                "factor": "Payment Discipline",
                "score": score.payment_discipline_score,
                "weight": "25%",
                "contribution": round((score.payment_discipline_score or 0) * 0.25, 1),
                "explanation": f"Bounce count: {signals.get('bounce_count', 0)} — "
                               f"{'excellent' if signals.get('bounce_count', 0) == 0 else 'concerning'}"
            },
            {
                "factor": "Revenue Consistency",
                "score": score.revenue_growth_score,
                "weight": "20%",
                "contribution": round((score.revenue_growth_score or 0) * 0.20, 1),
                "explanation": f"Consistency score: {signals.get('consistency_score', 0):.0f}/100"
            },
            {
                "factor": "GST Compliance",
                "score": score.gst_compliance_score,
                "weight": "12%",
                "contribution": round((score.gst_compliance_score or 0) * 0.12, 1),
                "explanation": "GST filing regularity + bank vs GST revenue match"
            },
            {
                "factor": "Business Vintage",
                "score": score.business_vintage_score,
                "weight": "8%",
                "contribution": round((score.business_vintage_score or 0) * 0.08, 1),
                "explanation": "Business age and stability"
            }
        ],
        "risk_flags": [
            {
                "flag": flag,
                "severity": "high" if flag in ["high_bounce_rate", "gst_bank_mismatch"] else "medium",
                "impact": "Score reduced by ~15-20 points"
            }
            for flag in (score.flags or [])
        ],
        "data_quality": {
            "months_of_data": score.data_months,
            "confidence": float(score.confidence or 0),
            "sufficient": (score.data_months or 0) >= 6
        }
    }


# ─── Rejection Tracking ───────────────────────────────────────────

class RejectionCreate(BaseModel):
    business_id: str
    rejection_reason: str
    rejection_detail: str
    rejected_by: str = "lender"
    improvement_needed: Optional[dict] = None


@router.post("/reject")
def log_rejection(
    payload: RejectionCreate,
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """Log a rejection — feeds model improvement loop."""
    bid = UUID(payload.business_id)

    score = db.query(RiskScore).filter(RiskScore.business_id == bid).first()

    rejection = RejectionLog(
        business_id=bid,
        lender_id=lender.id,
        score_at_rejection=score.score if score else None,
        grade_at_rejection=score.grade if score else None,
        rejection_reason=payload.rejection_reason,
        rejection_detail=payload.rejection_detail,
        rejected_by=payload.rejected_by,
        improvement_needed=payload.improvement_needed or {}
    )
    db.add(rejection)
    db.commit()

    logger.info(f"Rejection logged: {payload.business_id} — {payload.rejection_reason}")

    # ✅ Audit log — lender rejected a business
    log_audit(
        db, lender.id,
        business_id=payload.business_id,
        action="rejected_business",
        endpoint="/v1/lender/reject"
    )

    return {
        "logged": True,
        "rejection_id": str(rejection.id),
        "message": "Rejection recorded. This improves our scoring model."
    }


# ─── Manual Review Layer ──────────────────────────────────────────

@router.get("/review/queue")
def get_review_queue(
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """Manual review queue — borderline cases 600-720 score."""
    borderline = db.query(RiskScore, Business).join(
        Business, RiskScore.business_id == Business.id
    ).filter(
        RiskScore.score >= 600,
        RiskScore.score <= 720
    ).order_by(RiskScore.score.desc()).limit(50).all()

    queue = []
    for score, business in borderline:
        reviewed = db.query(RejectionLog).filter(
            RejectionLog.business_id == business.id,
            RejectionLog.reviewed_at.isnot(None)
        ).first()

        queue.append({
            "business_id": str(business.id),
            "business_name": business.business_name,
            "city": business.city,
            "score": score.score,
            "grade": score.grade,
            "flags": score.flags or [],
            "recommended_limit": float(score.recommended_limit or 0),
            "review_status": "reviewed" if reviewed else "pending",
            "review_notes": reviewed.review_notes if reviewed else None
        })

    # ✅ Audit log — lender accessed review queue
    log_audit(
        db, lender.id,
        action="viewed_review_queue",
        endpoint="/v1/lender/review/queue"
    )

    return {
        "queue_size": len(queue),
        "pending": sum(1 for q in queue if q["review_status"] == "pending"),
        "reviewed": sum(1 for q in queue if q["review_status"] == "reviewed"),
        "cases": queue
    }


class ReviewUpdate(BaseModel):
    business_id: str
    decision: str       # approve, reject, more_info
    review_notes: str
    reviewed_by: str


@router.post("/review/submit")
def submit_review(
    payload: ReviewUpdate,
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """Submit manual review decision."""
    bid = UUID(payload.business_id)

    if payload.decision == "reject":
        rejection = RejectionLog(
            business_id=bid,
            lender_id=lender.id,
            rejection_reason="manual_review_rejection",
            rejection_detail=payload.review_notes,
            rejected_by="manual_review",
            reviewed_by=payload.reviewed_by,
            review_notes=payload.review_notes,
            reviewed_at=datetime.utcnow()
        )
        db.add(rejection)
        db.commit()

    logger.info(f"Manual review: {payload.business_id} — {payload.decision} by {payload.reviewed_by}")

    # ✅ Audit log — manual review submitted
    log_audit(
        db, lender.id,
        business_id=payload.business_id,
        action=f"manual_review_{payload.decision}",
        endpoint="/v1/lender/review/submit"
    )

    return {
        "decision": payload.decision,
        "business_id": payload.business_id,
        "reviewed_by": payload.reviewed_by,
        "message": f"Review submitted: {payload.decision}"
    }


# ─── Portfolio Health ─────────────────────────────────────────────

@router.get("/portfolio")
def get_portfolio_health(
    lender: Lender = Depends(get_lender),
    db: Session = Depends(get_db)
):
    """Portfolio health for lender's active loans."""
    active_loans = db.query(LoanOffer).filter(
        LoanOffer.lender_id == lender.id,
        LoanOffer.status.in_(["accepted", "disbursed"])
    ).all()

    total_deployed = sum(float(l.offered_amount) for l in active_loans)
    our_fees = sum(float(l.our_fee_amount or 0) for l in active_loans)

    # ✅ Audit log — lender viewed portfolio
    log_audit(
        db, lender.id,
        action="viewed_portfolio",
        endpoint="/v1/lender/portfolio"
    )

    return {
        "lender": lender.name,
        "active_loans": len(active_loans),
        "total_deployed": total_deployed,
        "our_origination_fees": our_fees,
        "portfolio_summary": {
            "accepted": sum(1 for l in active_loans if l.status == "accepted"),
            "disbursed": sum(1 for l in active_loans if l.status == "disbursed"),
        }
    }