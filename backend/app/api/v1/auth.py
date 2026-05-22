from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.business import Business
from app.utils.security import create_access_token, create_refresh_token
import uuid

router = APIRouter()

# --- Schemas ---
class RegisterRequest(BaseModel):
    pan: str
    gstin: Optional[str] = None
    business_name: str
    owner_name: str
    owner_phone: str
    owner_email: Optional[str] = None
    business_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

class LoginRequest(BaseModel):
    owner_phone: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    business_id: str

# --- Endpoints ---

@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Check if already registered
    existing = db.query(Business).filter(Business.pan == payload.pan).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business with this PAN already registered"
        )

    # Create new business
    business = Business(
        pan=payload.pan.upper(),
        gstin=payload.gstin,
        business_name=payload.business_name,
        owner_name=payload.owner_name,
        owner_phone=payload.owner_phone,
        owner_email=payload.owner_email,
        business_type=payload.business_type,
        city=payload.city,
        state=payload.state,
        status="active",
        onboarding_step=1
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    # Issue tokens
    token_data = {"sub": str(business.id), "phone": business.owner_phone}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        business_id=str(business.id)
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    business = db.query(Business).filter(
        Business.owner_phone == payload.owner_phone
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No business found with this phone number"
        )

    token_data = {"sub": str(business.id), "phone": business.owner_phone}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        business_id=str(business.id)
    )


@router.get("/me")
def get_me(db: Session = Depends(get_db)):
    # Placeholder — will add JWT auth dependency next
    return {"message": "authenticated endpoint - coming next"}