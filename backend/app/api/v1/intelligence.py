from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.models.risk_score import RiskScore
from app.agents.pipeline import run_intelligence_pipeline
from app.services.notification import notify_score_ready
from uuid import UUID

from app.models.business import Business

router = APIRouter()

class ScoreRequest(BaseModel):
    business_id: str

@router.post("/score")
def compute_score(payload: ScoreRequest, db: Session = Depends(get_db)):
    result = run_intelligence_pipeline(payload.business_id, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # WhatsApp notification — score ready
    business = db.query(Business).filter(
        Business.id == UUID(payload.business_id)
    ).first()

    if business and business.owner_phone:
        notify_score_ready(
            phone=business.owner_phone,
            business_name=business.business_name,
            score=result["score"],
            grade=result["grade"],
            limit=result["recommended_limit"]
        )

    return result

@router.get("/score/{business_id}")
def get_score(business_id: str, db: Session = Depends(get_db)):
    """Get existing credit score for a business."""
    score = db.query(RiskScore).filter(
        RiskScore.business_id == UUID(business_id)
    ).first()
    if not score:
        raise HTTPException(status_code=404, detail="No score found. Run POST /score first.")
    return {
        "score": score.score,
        "grade": score.grade,
        "cash_flow_score": score.cash_flow_score,
        "payment_discipline_score": score.payment_discipline_score,
        "gst_compliance_score": score.gst_compliance_score,
        "recommended_limit": float(score.recommended_limit),
        "recommended_tenure_months": score.recommended_tenure_months,
        "flags": score.flags,
        "positive_factors": score.positive_factors,
        "improvement_areas": score.improvement_areas,
        "confidence": float(score.confidence),
        "computed_at": score.computed_at
    }