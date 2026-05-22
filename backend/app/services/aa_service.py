import uuid
from datetime import datetime, timedelta
from app.utils.logger import get_logger

logger = get_logger(__name__)

# -------------------------------------------------------------------
# MOCK AA SERVICE — Real Setu se swap karna hai baad mein
# KYC complete hone ke baad sirf SETU_MODE = True karo
# -------------------------------------------------------------------
SETU_MODE = False  # True karo jab Setu KYC complete ho


async def create_consent(business_id: str, phone: str) -> dict:
    if SETU_MODE:
        # Real Setu call — baad mein enable karenge
        pass

    # Mock response — exactly jaisa Setu deta hai
    consent_id = str(uuid.uuid4())
    logger.info(f"[MOCK] Consent created for {business_id}")
    return {
        "consent_id": consent_id,
        "consent_url": f"https://mock-setu.com/consent/{consent_id}",
        "status": "PENDING"
    }


async def fetch_consent_status(consent_id: str) -> dict:
    return {
        "id": consent_id,
        "status": "ACTIVE"
    }


async def fetch_financial_data(business_id: str) -> dict:
    """
    Mock bank statement data — realistic textile trader profile
    Rajesh Sharma, Surat textile trader, ₹45L/month turnover
    """
    logger.info(f"[MOCK] Fetching financial data for {business_id}")

    now = datetime.utcnow()
    transactions = []

    # Generate 12 months of realistic transactions
    for month in range(12):
        base_date = now - timedelta(days=30 * month)

        # Monthly customer receipts (credits) — textile buyers paying
        transactions += [
            {
                "txn_date": (base_date - timedelta(days=5)).strftime("%Y-%m-%d"),
                "amount": 1850000,  # ₹18.5L
                "txn_type": "CREDIT",
                "narration": "NEFT/Mehta Fabrics Pvt Ltd/Invoice Payment",
                "balance": 2100000,
                "category": "customer_receipt",
                "counterparty": "Mehta Fabrics Pvt Ltd"
            },
            {
                "txn_date": (base_date - timedelta(days=12)).strftime("%Y-%m-%d"),
                "amount": 1200000,  # ₹12L
                "txn_type": "CREDIT",
                "narration": "IMPS/Patel Garments/Trade Payment",
                "balance": 1800000,
                "category": "customer_receipt",
                "counterparty": "Patel Garments"
            },
            {
                "txn_date": (base_date - timedelta(days=18)).strftime("%Y-%m-%d"),
                "amount": 980000,  # ₹9.8L
                "txn_type": "CREDIT",
                "narration": "RTGS/Shah Exports Ltd",
                "balance": 1500000,
                "category": "customer_receipt",
                "counterparty": "Shah Exports Ltd"
            },
            # Supplier payments (debits)
            {
                "txn_date": (base_date - timedelta(days=8)).strftime("%Y-%m-%d"),
                "amount": 850000,  # ₹8.5L
                "txn_type": "DEBIT",
                "narration": "NEFT/Arvind Mills/Fabric Purchase",
                "balance": 1200000,
                "category": "supplier_payment",
                "counterparty": "Arvind Mills"
            },
            {
                "txn_date": (base_date - timedelta(days=22)).strftime("%Y-%m-%d"),
                "amount": 450000,
                "txn_type": "DEBIT",
                "narration": "NEFT/GST Payment/GSTN",
                "balance": 900000,
                "category": "tax_payment",
                "counterparty": "GSTN"
            },
            {
                "txn_date": (base_date - timedelta(days=25)).strftime("%Y-%m-%d"),
                "amount": 280000,
                "txn_type": "DEBIT",
                "narration": "Staff Salary/Monthly",
                "balance": 750000,
                "category": "salary",
                "counterparty": "Staff"
            },
        ]

    return {
        "account": {
            "bank_name": "HDFC Bank",
            "account_type": "current",
            "masked_account": "XXXX4521",
            "ifsc": "HDFC0001234"
        },
        "transactions": transactions,
        "summary": {
            "avg_monthly_credits": 4030000,   # ₹40.3L avg monthly credits
            "avg_monthly_debits": 1580000,    # ₹15.8L avg monthly debits
            "avg_monthly_balance": 1200000,   # ₹12L avg balance
            "bounce_count_12m": 0,            # Zero bounces — good sign
            "total_months": 12
        }
    }


async def get_session_data(session_id: str) -> dict:
    return {"status": "COMPLETED", "sessionId": session_id}