from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business import Business
from app.models.loan_offer import Lender, LoanOffer
from app.models.risk_score import RiskScore
from app.services.notification import notify_loan_accepted
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class LoanApplyRequest(BaseModel):
    business_id: str
    amount: float
    purpose: str
    tenure: Optional[int] = 12
    collateral: Optional[str] = "none"
    collateral_value: Optional[float] = None
    business_desc: Optional[str] = None
    monthly_revenue: Optional[float] = None


class AcceptOfferRequest(BaseModel):
    business_id: str
    lender_name: str
    amount: float
    rate: float


@router.post("/apply")
def apply_for_loan(payload: LoanApplyRequest, db: Session = Depends(get_db)):
    try:
        business_uuid = UUID(payload.business_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid business_id")

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Loan amount must be greater than 0")
    if not payload.purpose.strip():
        raise HTTPException(status_code=400, detail="Loan purpose is required")

    score = db.query(RiskScore).filter(RiskScore.business_id == business_uuid).first()
    if not score:
        # Keep application flow unblocked even before intelligence pipeline runs.
        score_value = 650
        recommended_limit = 2500000
    else:
        score_value = int(score.score or 650)
        recommended_limit = float(score.recommended_limit or 2500000)

    capped_amount = min(payload.amount, recommended_limit)
    indicative_rate = 13.5 if score_value >= 750 else 14.5 if score_value >= 700 else 16.0
    application_id = str(uuid4())

    logger.info(
        "Loan application received | business=%s | amount=%s | purpose=%s",
        payload.business_id,
        payload.amount,
        payload.purpose,
    )

    return {
        "status": "submitted",
        "application_id": application_id,
        "business_id": payload.business_id,
        "requested_amount": payload.amount,
        "approved_upto": capped_amount,
        "tenure_months": payload.tenure or 12,
        "purpose": payload.purpose,
        "score": score_value,
        "indicative_rate": indicative_rate,
        "message": "Application submitted. Matching lenders will contact you shortly.",
    }


@router.post("/offers/generate")
def generate_offers(business_id: str, db: Session = Depends(get_db)):
    score = db.query(RiskScore).filter(RiskScore.business_id == UUID(business_id)).first()
    if not score:
        raise HTTPException(status_code=404, detail="No score found")

    limit = float(score.recommended_limit)

    offers = [
        {
            "lender": "Lendingkart NBFC",
            "amount": min(limit, 7500000),
            "rate": 13.5,
            "tenure": 12,
            "processing_fee": 1.0,
            "featured": True,
        },
        {
            "lender": "Kotak Mahindra Bank",
            "amount": min(limit * 0.75, 6000000),
            "rate": 14.2,
            "tenure": 12,
            "processing_fee": 0.8,
            "featured": False,
        },
        {
            "lender": "HDFC Overdraft",
            "amount": min(limit * 0.6, 5000000),
            "rate": 15.0,
            "tenure": 0,
            "processing_fee": 0.5,
            "featured": False,
        },
    ]

    return {"business_id": business_id, "offers": offers, "score": score.score}


@router.post("/accept")
def accept_offer(payload: AcceptOfferRequest, db: Session = Depends(get_db)):
    score = db.query(RiskScore).filter(RiskScore.business_id == UUID(payload.business_id)).first()
    if not score:
        raise HTTPException(status_code=404, detail="No score found")

    lender = db.query(Lender).filter(Lender.name == payload.lender_name).first()
    if not lender:
        lender = Lender(
            name=payload.lender_name,
            type="nbfc",
            min_score=600,
            interest_rate_min=payload.rate,
            interest_rate_max=payload.rate + 2,
            is_active=True,
        )
        db.add(lender)
        db.commit()
        db.refresh(lender)

    if payload.rate > 0:
        monthly_rate = payload.rate / 100 / 12
        tenure = 12
        emi = (
            payload.amount
            * monthly_rate
            * (1 + monthly_rate) ** tenure
            / ((1 + monthly_rate) ** tenure - 1)
        )
    else:
        emi = 0

    our_fee = payload.amount * 0.01

    offer = LoanOffer(
        business_id=UUID(payload.business_id),
        lender_id=lender.id,
        risk_score_id=score.id,
        offered_amount=payload.amount,
        interest_rate=payload.rate,
        tenure_months=12,
        processing_fee=payload.amount * 0.01,
        emi_amount=emi,
        status="accepted",
        offer_expires_at=datetime.utcnow() + timedelta(days=7),
        our_fee_amount=our_fee,
        our_fee_pct=1.0,
        accepted_at=datetime.utcnow(),
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)

    logger.info(f"Offer accepted: {payload.lender_name} INR {payload.amount:,.0f} for {payload.business_id}")
    logger.info(f"Our origination fee: INR {our_fee:,.0f}")

    business = db.query(Business).filter(Business.id == UUID(payload.business_id)).first()
    if business and business.owner_phone:
        notify_loan_accepted(
            phone=business.owner_phone,
            business_name=business.business_name,
            lender=payload.lender_name,
            amount=payload.amount,
            rate=payload.rate,
        )
        logger.info(f"WhatsApp notification sent to {business.owner_phone}")
    else:
        logger.warning(f"No phone found for business {payload.business_id}. Notification skipped.")

    return {
        "status": "accepted",
        "offer_id": str(offer.id),
        "lender": payload.lender_name,
        "amount": payload.amount,
        "rate": payload.rate,
        "emi": round(emi),
        "our_fee": our_fee,
        "message": f"Offer accepted. {payload.lender_name} will contact you within 24 hours.",
        "next_steps": [
            "Lender will verify your KYC documents",
            "Bank statement verification",
            "Loan agreement signing",
            "Disbursement within 3-5 business days",
        ],
    }


@router.get("/history/{business_id}")
def get_loan_history(business_id: str, db: Session = Depends(get_db)):
    offers = db.query(LoanOffer).filter(LoanOffer.business_id == UUID(business_id)).all()

    return {
        "total_offers": len(offers),
        "accepted": [
            {
                "offer_id": str(o.id),
                "lender_id": str(o.lender_id),
                "amount": float(o.offered_amount),
                "rate": float(o.interest_rate),
                "status": o.status,
                "accepted_at": str(o.accepted_at),
            }
            for o in offers
            if o.status == "accepted"
        ],
        "disbursed": [
            {
                "offer_id": str(o.id),
                "amount": float(o.offered_amount),
                "disbursed_at": str(o.disbursed_at),
            }
            for o in offers
            if o.status == "disbursed"
        ],
    }
