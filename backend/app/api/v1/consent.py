from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.consent import Consent
from app.models.business import Business
from app.utils.logger import get_logger
import uuid
import os

router = APIRouter()
logger = get_logger(__name__)

# Check if real AA is configured
AA_CONFIGURED = bool(os.getenv("PERFIOS_API_KEY") or os.getenv("SETU_CLIENT_ID"))


class ConsentInitiateRequest(BaseModel):
    business_id: str
    phone: str


@router.post("/initiate")
async def initiate_consent(
    payload: ConsentInitiateRequest,
    db: Session = Depends(get_db)
):
    """
    Start AA consent flow.
    If AA not configured → direct to CSV upload (fastest path).
    """
    business = db.query(Business).filter(
        Business.id == uuid.UUID(payload.business_id)
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # ── If real AA configured — use it ──────────────────────────────────────
    if AA_CONFIGURED:
        try:
            from app.services.perfios_service import create_consent_request
            result = await create_consent_request(
                mobile=payload.phone,
                business_id=payload.business_id,
                redirect_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/v1/consent/callback"
            )

            consent = Consent(
                business_id=uuid.UUID(payload.business_id),
                aa_consent_id=result["consent_id"],
                consent_types=["PROFILE", "SUMMARY", "TRANSACTIONS"],
                data_date_from=datetime.utcnow() - timedelta(days=365),
                data_date_to=datetime.utcnow(),
                status="pending",
                expires_at=datetime.utcnow() + timedelta(days=180),
                purpose="credit_assessment"
            )
            db.add(consent)
            db.commit()
            db.refresh(consent)

            return {
                "consent_id":   result["consent_id"],
                "redirect_url": result["consent_url"],
                "source":       "perfios_aa",
                "message":      "Redirect user to consent_url to approve data sharing"
            }
        except Exception as e:
            logger.error(f"AA consent failed: {e}")
            # Fall through to CSV path

    # ── AA not configured — CSV upload path (fastest) ────────────────────────
    logger.info(f"AA not configured — using CSV path for {payload.business_id}")

    # Create a "pending_csv" consent record so system knows data is expected
    existing = db.query(Consent).filter(
        Consent.business_id == uuid.UUID(payload.business_id)
    ).first()

    if not existing:
        consent = Consent(
            business_id=uuid.UUID(payload.business_id),
            aa_consent_id=f"csv_{payload.business_id[:8]}",
            consent_types=["TRANSACTIONS"],
            data_date_from=datetime.utcnow() - timedelta(days=365),
            data_date_to=datetime.utcnow(),
            status="pending_csv",
            expires_at=datetime.utcnow() + timedelta(days=180),
            purpose="credit_assessment"
        )
        db.add(consent)
        db.commit()

    return {
        "status":           "csv_required",
        "source":           "csv_upload",
        "message":          "Bank statement CSV upload karo — instant processing hoga",
        "upload_endpoint":  "POST /v1/upload/bank-statement",
        "instructions":     "Apne bank se last 12 months ka statement download karo (CSV/Excel) aur upload karo",
        "supported_banks":  ["HDFC", "SBI", "ICICI", "Axis", "Kotak", "PNB", "BOB"],
        "next_step":        "Upload ke baad POST /v1/data/fetch call karo"
    }


@router.get("/callback")
async def consent_callback(request: Request, db: Session = Depends(get_db)):
    """AA redirects here after MSME approves/rejects."""
    params      = dict(request.query_params)
    consent_id  = params.get("consentId") or params.get("id")
    status      = params.get("status", "unknown")

    logger.info(f"Consent callback: {params}")

    if consent_id:
        consent = db.query(Consent).filter(
            Consent.aa_consent_id == consent_id
        ).first()
        if consent:
            consent.status = "active" if status == "ACTIVE" else "rejected"
            db.commit()

    return {"message": f"Consent {status}", "consent_id": consent_id}


@router.post("/webhook")
async def consent_webhook(request: Request, db: Session = Depends(get_db)):
    """AA webhook notifications."""
    body       = await request.json()
    event_type = body.get("type")
    consent_id = body.get("consentId")

    logger.info(f"Consent webhook: {event_type} — {consent_id}")

    if event_type == "CONSENT_STATUS_UPDATE" and consent_id:
        consent = db.query(Consent).filter(
            Consent.aa_consent_id == consent_id
        ).first()
        if consent:
            new_status   = body.get("data", {}).get("status", "").lower()
            consent.status = new_status
            db.commit()
            logger.info(f"Consent {consent_id} → {new_status}")

    return {"status": "ok"}


@router.get("/status/{business_id}")
def get_consent_status(business_id: str, db: Session = Depends(get_db)):
    """Check consent + data status for a business."""
    from app.models.bank_data import BankTransaction

    consent = db.query(Consent).filter(
        Consent.business_id == uuid.UUID(business_id)
    ).first()

    txn_count = db.query(BankTransaction).filter(
        BankTransaction.business_id == uuid.UUID(business_id)
    ).count()

    if not consent:
        return {
            "status":      "no_consent",
            "has_data":    False,
            "txn_count":   0,
            "next_action": "POST /v1/consent/initiate",
        }

    return {
        "consent_id":  str(consent.aa_consent_id),
        "status":      consent.status,
        "has_data":    txn_count > 0,
        "txn_count":   txn_count,
        "created_at":  consent.created_at,
        "next_action": None if txn_count > 0 else "POST /v1/upload/bank-statement",
    }