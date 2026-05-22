from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business import Business
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class BusinessProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pan_number: Optional[str] = None
    gstin: Optional[str] = None
    mobile: Optional[str] = None
    business_name: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pan_verified: Optional[bool] = None
    gstin_verified: Optional[bool] = None
    kyc_score: Optional[int] = None


@router.put("/{business_id}/profile")
def update_business_profile(
    business_id: str,
    payload: BusinessProfileUpdate,
    db: Session = Depends(get_db),
):
    try:
        business_uuid = UUID(business_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid business_id")

    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if payload.pan_number:
        business.pan = payload.pan_number.upper().strip()
    if payload.gstin is not None:
        business.gstin = payload.gstin.upper().strip() if payload.gstin else None
    if payload.mobile:
        business.owner_phone = payload.mobile.strip()
    if payload.business_name:
        business.business_name = payload.business_name.strip()
    if payload.owner_name:
        business.owner_name = payload.owner_name.strip()
    if payload.owner_email is not None:
        business.owner_email = payload.owner_email.strip() or None
    if payload.city is not None:
        business.city = payload.city.strip() or None
    if payload.state is not None:
        business.state = payload.state.strip() or None

    if business.onboarding_step is None:
        business.onboarding_step = 2
    else:
        business.onboarding_step = max(business.onboarding_step, 2)

    try:
        db.commit()
        db.refresh(business)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="PAN or GSTIN already used by another business")
    except Exception:
        db.rollback()
        logger.exception("Failed to update business profile")
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return {
        "status": "saved",
        "business_id": str(business.id),
        "business_name": business.business_name,
        "pan": business.pan,
        "gstin": business.gstin,
        "owner_phone": business.owner_phone,
        "onboarding_step": business.onboarding_step,
    }
