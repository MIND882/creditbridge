"""
KYC Service — Surepass Sandbox Integration
Sandbox:    https://sandbox.surepass.io
Production: https://kyc-api.surepass.app

Verified Endpoints (from docs):
  PAN:   POST /api/v1/pan/pan-comprehensive
  GSTIN: POST /api/v1/corporate/gstin        ✅ FIXED
"""

import httpx
from typing import Optional
from app.config import Settings

settings       = Settings()
SUREPASS_TOKEN = settings.SUREPASS_API_TOKEN
SUREPASS_BASE  = settings.SUREPASS_BASE_URL


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {SUREPASS_TOKEN}",
        "Content-Type":  "application/json",
    }


# ─── PAN Comprehensive ────────────────────────────────────────────────────────
async def verify_pan_comprehensive(pan_number: str) -> dict:
    """POST /api/v1/pan/pan-comprehensive"""
    url = f"{SUREPASS_BASE}/api/v1/pan/pan-comprehensive"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res  = await client.post(
                url,
                headers=_headers(),
                json={
                    "id_number":              pan_number.upper().strip(),
                    "masked_aadhaar_variant": "v1, v2, empty",
                }
            )
            data = res.json()

            if not data.get("success"):
                return {
                    "verified": False,
                    "error":    data.get("message", "PAN verification failed"),
                    "pan":      pan_number,
                }

            d = data.get("data", {})
            return {
                "verified":        True,
                "pan":             d.get("pan_number"),
                "full_name":       d.get("full_name"),
                "full_name_split": d.get("full_name_split"),
                "dob":             d.get("dob"),
                "gender":          d.get("gender"),
                "category":        d.get("category"),
                "aadhaar_linked":  d.get("aadhaar_linked"),
                "masked_aadhaar":  d.get("masked_aadhaar"),
                "email":           d.get("email"),
                "phone_number":    d.get("phone_number"),
                "address":         d.get("address"),
                "dob_verified":    d.get("dob_verified"),
                "client_id":       d.get("client_id"),
            }

    except httpx.TimeoutException:
        return {"verified": False, "error": "Timeout — Surepass se response nahi aaya"}
    except Exception as e:
        return {"verified": False, "error": str(e)}


# ─── PAN Name Quick ───────────────────────────────────────────────────────────
async def verify_pan_name(pan_number: str) -> dict:
    """POST /api/v1/pan/pan"""
    url = f"{SUREPASS_BASE}/api/v1/pan/pan"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res  = await client.post(
                url,
                headers=_headers(),
                json={"id_number": pan_number.upper().strip()}
            )
            data = res.json()
            d    = data.get("data", {})
            return {
                "verified":  data.get("success", False),
                "pan":       pan_number,
                "full_name": d.get("full_name"),
                "error":     None if data.get("success") else data.get("message"),
            }
    except Exception as e:
        return {"verified": False, "error": str(e)}


# ─── Corporate GSTIN ──────────────────────────────────────────────────────────
async def verify_gstin(gstin: str) -> dict:
    """
    POST /api/v1/corporate/gstin   ✅ CORRECT URL (from docs)

    Response fields (from docs):
      business_name  → trade name
      legal_name     → registered owner name
      gstin_status   → "Active" / "Inactive"
    """
    url = f"{SUREPASS_BASE}/api/v1/corporate/gstin"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res  = await client.post(
                url,
                headers=_headers(),
                json={"id_number": gstin.upper().strip()}
            )
            data = res.json()

            if not data.get("success"):
                return {
                    "verified": False,
                    "error":    data.get("message", "GSTIN verification failed"),
                    "gstin":    gstin,
                }

            d = data.get("data", {})
            return {
                "verified":               True,
                "gstin":                  d.get("gstin"),
                "pan_number":             d.get("pan_number"),
                "business_name":          d.get("business_name"),   # trade name
                "legal_name":             d.get("legal_name"),       # owner name
                "gstin_status":           d.get("gstin_status"),     # "Active"
                "registration_date":      d.get("date_of_registration"),
                "business_type":          d.get("constitution_of_business"),
                "taxpayer_type":          d.get("taxpayer_type"),
                "center_jurisdiction":    d.get("center_jurisdiction"),
                "state_jurisdiction":     d.get("state_jurisdiction"),
                "nature_bus_activities":  d.get("nature_bus_activities", []),
                "aadhaar_validation":     d.get("aadhaar_validation"),
                "address":                d.get("address"),
                "client_id":              d.get("client_id"),
            }

    except httpx.TimeoutException:
        return {"verified": False, "error": "Timeout"}
    except Exception as e:
        return {"verified": False, "error": str(e)}


# ─── Digilocker ───────────────────────────────────────────────────────────────
async def generate_digilocker_link(
    name:   str,
    dob:    str,
    mobile: Optional[str] = None
) -> dict:
    """POST /api/v1/digilocker/digilocker"""
    url     = f"{SUREPASS_BASE}/api/v1/digilocker/digilocker"
    payload = {"name": name, "dob": dob}
    if mobile:
        payload["mobile"] = mobile

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res  = await client.post(url, headers=_headers(), json=payload)
            data = res.json()
            d    = data.get("data", {})
            return {
                "success":        data.get("success", False),
                "digilocker_url": d.get("url"),
                "request_id":     d.get("request_id"),
                "error":          None if data.get("success") else data.get("message"),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Combined MSME KYC ────────────────────────────────────────────────────────
async def verify_msme_kyc(pan: str, gstin: str) -> dict:
    """PAN + GSTIN ek saath — full KYC package for lender"""
    pan_result   = await verify_pan_comprehensive(pan)
    gstin_result = await verify_gstin(gstin)

    both_verified = pan_result.get("verified") and gstin_result.get("verified")

    name_match = False
    if both_verified:
        pan_name   = (pan_result.get("full_name")   or "").lower().strip()
        gstin_name = (gstin_result.get("legal_name") or "").lower().strip()
        if pan_name:
            name_match = pan_name.split()[0] in gstin_name

    return {
        "kyc_passed": both_verified,
        "name_match": name_match,
        "kyc_score":  _compute_kyc_score(pan_result, gstin_result),
        "pan":        pan_result,
        "gstin":      gstin_result,
    }


def _compute_kyc_score(pan: dict, gstin: dict) -> int:
    """KYC trust score 0-100"""
    score = 0
    if pan.get("verified"):                      score += 40
    if pan.get("aadhaar_linked"):                score += 20
    if gstin.get("verified"):                    score += 25
    if gstin.get("gstin_status") == "Active":    score += 15  # ✅ "Active" not "ACTIVE"
    return score