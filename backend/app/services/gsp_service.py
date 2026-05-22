"""
GSP Service — GST Suvidha Provider Integration
Real GST return data for MSME credit scoring
"""
import httpx
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

GSP_BASE   = os.getenv("GSP_BASE_URL",  "https://api.mastergst.com")
GSP_KEY    = os.getenv("GSP_API_KEY",   "")
GSP_SECRET = os.getenv("GSP_SECRET",    "")


def _headers() -> dict:
    return {
        "client_id":     GSP_KEY,
        "client_secret": GSP_SECRET,
        "Content-Type":  "application/json",
    }


# ─── GSTIN Details ────────────────────────────────────────────────────────────
async def fetch_gstin_details(gstin: str) -> dict:
    """Fetch business details from GST portal"""
    if not GSP_KEY:
        return _mock_gstin(gstin)

    url = f"{GSP_BASE}/commonapi/v1.1/search?action=TP&gstin={gstin}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res  = await client.get(url, headers=_headers())
            data = res.json()
            return {
                "gstin":         data.get("gstin"),
                "legal_name":    data.get("lgnm"),
                "trade_name":    data.get("tradeNam"),
                "status":        data.get("sts"),
                "business_type": data.get("ctb"),
                "reg_date":      data.get("rgdt"),
                "address":       _format_address(data.get("pradr", {})),
            }
    except Exception as e:
        logger.error(f"GSP GSTIN error: {e}")
        return _mock_gstin(gstin)


# ─── GSTR-3B Returns ─────────────────────────────────────────────────────────
async def fetch_gstr3b(gstin: str, months: int = 12) -> dict:
    """
    Fetch GSTR-3B filings — shows revenue + tax paid
    Key signal for creditworthiness
    """
    if not GSP_KEY:
        return _mock_gstr3b(gstin)

    url = f"{GSP_BASE}/ei/api/gstr3b"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res  = await client.get(url, headers=_headers(), params={
                "gstin": gstin, "ret_period": _last_n_periods(months)
            })
            data = res.json()
            filings = data.get("data", [])
            return {
                "gstin":         gstin,
                "filings":       filings,
                "total_turnover": sum(f.get("sup_details", {}).get("osup_zero", {}).get("txval", 0) for f in filings),
                "filing_count":  len(filings),
                "compliance":    _compliance_score(filings, months),
                "source":        "gsp_live",
            }
    except Exception as e:
        logger.error(f"GSP GSTR3B error: {e}")
        return _mock_gstr3b(gstin)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _compliance_score(filings: list, expected: int) -> int:
    if expected == 0: return 0
    return min(100, int(len(filings) / expected * 100))

def _format_address(addr: dict) -> str:
    parts = [addr.get("bnm",""), addr.get("loc",""), addr.get("dst",""), addr.get("stcd","")]
    return ", ".join(p for p in parts if p)

def _last_n_periods(n: int) -> str:
    import datetime
    today = datetime.date.today()
    return f"{(today.month-n)%12+1:02d}{today.year}"

def _mock_gstin(gstin: str) -> dict:
    return {
        "gstin": gstin, "legal_name": "Mock Business Pvt Ltd",
        "trade_name": "Mock Business", "status": "Active",
        "business_type": "Private Limited", "reg_date": "2020-01-01",
        "address": "Mumbai, Maharashtra", "source": "mock",
    }

def _mock_gstr3b(gstin: str) -> dict:
    import random
    filings = [{"period": f"{i:02d}2024", "turnover": round(random.uniform(200000, 1500000), 0)} for i in range(1, 13)]
    return {
        "gstin": gstin, "filings": filings,
        "total_turnover": sum(f["turnover"] for f in filings),
        "filing_count": 12, "compliance": 100, "source": "mock",
    }