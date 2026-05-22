"""
KYC API Routes — /api/v1/kyc/*
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.kyc_service import (
    verify_pan_comprehensive,
    verify_pan_name,
    verify_gstin,
    verify_msme_kyc,
    generate_digilocker_link,
)

router = APIRouter()


# ─── Request Models ───────────────────────────────────────────────────────────
class PANRequest(BaseModel):
    pan_number: str

class GSTINRequest(BaseModel):
    gstin: str

class MSMEKYCRequest(BaseModel):
    pan:   str
    gstin: str

class DigilockerRequest(BaseModel):
    name:   str
    dob:    str              # DD-MM-YYYY
    mobile: Optional[str] = None


# ─── Routes ──────────
# ─────────────────────────────────────────────────────────

@router.post("/pan")
async def pan_verify(req: PANRequest):
    """Full PAN verification — name, DOB, status, Aadhaar link"""
    if len(req.pan_number) != 10:
        raise HTTPException(status_code=400, detail="PAN 10 characters ka hona chahiye")
    result = await verify_pan_comprehensive(req.pan_number)
    if not result.get("verified"):
        raise HTTPException(status_code=422, detail=result.get("error", "PAN verify nahi hua"))
    return result


@router.post("/pan/quick")
async def pan_name_check(req: PANRequest):
    """Quick PAN name check"""
    return await verify_pan_name(req.pan_number)


@router.post("/gstin")
async def gstin_verify(req: GSTINRequest):
    """Corporate GSTIN verification"""
    if len(req.gstin) != 15:
        raise HTTPException(status_code=400, detail="GSTIN 15 characters ka hona chahiye")
    result = await verify_gstin(req.gstin)
    if not result.get("verified"):
        raise HTTPException(status_code=422, detail=result.get("error", "GSTIN verify nahi hua"))
    return result


@router.post("/msme")
async def msme_kyc(req: MSMEKYCRequest):
    """
    Full MSME KYC — PAN + GSTIN ek saath
    Lender ke liye complete KYC package
    """
    result = await verify_msme_kyc(req.pan, req.gstin)
    return result


@router.post("/digilocker")
async def digilocker_link(req: DigilockerRequest):
    """
    Digilocker verification link generate karo
    MSME ko link bhejo — woh Aadhaar verify karega
    """
    result = await generate_digilocker_link(req.name, req.dob, req.mobile)
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("error"))
    return result


# ─── Health check ─────────────────────────────────────────────────────────────
@router.get("/health")
async def kyc_health():
    """Check karo Surepass connected hai ya nahi"""
    import os
    token = os.getenv("SUREPASS_API_TOKEN")
    return {
        "status":     "ok" if token else "missing_token",
        "provider":   "Surepass",
        "sandbox":    True,
        "base_url":   os.getenv("SUREPASS_BASE_URL", "https://sandbox.surepass.app"),
        "apis_ready": ["pan", "pan_name", "gstin", "digilocker"]
    }