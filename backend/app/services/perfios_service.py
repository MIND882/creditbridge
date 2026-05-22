"""
Perfios Account Aggregator Service
Real bank transaction feed for MSME credit scoring
Docs: https://www.perfios.com/aa-developer
"""
import httpx
import os
from typing import Optional
from app.config import Settings
from app.utils.logger import get_logger

settings = Settings()
logger   = get_logger(__name__)

PERFIOS_BASE   = os.getenv("PERFIOS_BASE_URL",  "https://sandbox.perfios.com")
PERFIOS_KEY    = os.getenv("PERFIOS_API_KEY",    "")
PERFIOS_SECRET = os.getenv("PERFIOS_API_SECRET", "")


def _headers() -> dict:
    return {
        "x-api-key":    PERFIOS_KEY,
        "Content-Type": "application/json",
    }


# ─── Step 1: Create AA Consent Request ───────────────────────────────────────
async def create_consent_request(
    mobile: str,
    business_id: str,
    redirect_url: str,
) -> dict:
    """
    Creates AA consent link — send to MSME
    MSME approves → bank shares data with us
    """
    if not PERFIOS_KEY:
        logger.warning("Perfios not configured — returning mock")
        return _mock_consent(business_id)

    url = f"{PERFIOS_BASE}/v2/consent/create"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res  = await client.post(url, headers=_headers(), json={
                "mobile":       mobile,
                "purpose":      "Credit Assessment for MSME Loan",
                "redirectUrl":  redirect_url,
                "consentMode":  "STORE",
                "fetchType":    "PERIODIC",
                "frequency":    {"unit": "DAY", "value": 1},
                "dataRange":    {"from": "-12M", "to": "0D"},
                "fiTypes":      ["DEPOSIT", "SAVINGS", "CURRENT"],
                "metadata":     {"business_id": business_id},
            })
            data = res.json()
            return {
                "consent_id":   data.get("consentId"),
                "consent_url":  data.get("consentUrl"),
                "status":       "pending",
            }
    except Exception as e:
        logger.error(f"Perfios consent error: {e}")
        return _mock_consent(business_id)


# ─── Step 2: Fetch Bank Transactions ─────────────────────────────────────────
async def fetch_bank_transactions(
    consent_id: str,
    business_id: str,
) -> dict:
    """
    Fetch transactions after consent approved
    Returns processed transaction list
    """
    if not PERFIOS_KEY:
        logger.warning("Perfios not configured — returning mock data")
        return _mock_transactions(business_id)

    url = f"{PERFIOS_BASE}/v2/accounts/fetch"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res  = await client.post(url, headers=_headers(), json={
                "consentId":  consent_id,
                "fromDate":   _months_ago(12),
                "toDate":     _today(),
            })
            data = res.json()

            accounts     = data.get("accounts", [])
            transactions = []
            for acc in accounts:
                for txn in acc.get("transactions", []):
                    transactions.append({
                        "date":        txn.get("transactionTimestamp", "")[:10],
                        "amount":      float(txn.get("amount", 0)),
                        "type":        "CREDIT" if txn.get("type") == "CREDIT" else "DEBIT",
                        "description": txn.get("narration", ""),
                        "balance":     float(txn.get("currentBalance", 0)),
                        "account":     acc.get("maskedAccountNumber", ""),
                    })

            return {
                "business_id":   business_id,
                "transactions":  transactions,
                "total_credits": sum(t["amount"] for t in transactions if t["type"] == "CREDIT"),
                "total_debits":  sum(t["amount"] for t in transactions if t["type"] == "DEBIT"),
                "count":         len(transactions),
                "source":        "perfios_live",
            }

    except Exception as e:
        logger.error(f"Perfios fetch error: {e}")
        return _mock_transactions(business_id)


# ─── Mock Fallback ────────────────────────────────────────────────────────────
def _mock_consent(business_id: str) -> dict:
    return {
        "consent_id":  f"mock_consent_{business_id[:8]}",
        "consent_url": "https://sandbox.perfios.com/mock-consent",
        "status":      "mock",
        "note":        "Perfios not configured — mock response",
    }

def _mock_transactions(business_id: str) -> dict:
    import random, datetime
    txns = []
    base_date = datetime.date.today()
    for i in range(90):
        d = base_date - datetime.timedelta(days=i * 4)
        txns.append({
            "date":        str(d),
            "amount":      round(random.uniform(10000, 800000), 0),
            "type":        "CREDIT" if i % 3 != 0 else "DEBIT",
            "description": f"Mock transaction {i+1}",
            "balance":     round(random.uniform(50000, 2000000), 0),
            "account":     "XXXX4521",
        })
    return {
        "business_id":   business_id,
        "transactions":  txns,
        "total_credits": sum(t["amount"] for t in txns if t["type"] == "CREDIT"),
        "total_debits":  sum(t["amount"] for t in txns if t["type"] == "DEBIT"),
        "count":         len(txns),
        "source":        "mock",
    }

def _today() -> str:
    import datetime
    return str(datetime.date.today())

def _months_ago(n: int) -> str:
    import datetime
    d = datetime.date.today().replace(month=max(1, datetime.date.today().month - n))
    return str(d)