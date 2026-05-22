from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.models.bank_data import BankAccount, BankTransaction
from app.models.consent import Consent
from app.models.business import Business
from app.utils.logger import get_logger
from datetime import datetime
import uuid
import os

router = APIRouter()
logger = get_logger(__name__)

AA_CONFIGURED = bool(os.getenv("PERFIOS_API_KEY") or os.getenv("SETU_CLIENT_ID"))


class FetchDataRequest(BaseModel):
    business_id: str


@router.post("/fetch")
async def fetch_data(
    payload: FetchDataRequest,
    db: Session = Depends(get_db)
):
    """
    Fetch bank data.
    Priority:
      1. Already in DB (from CSV upload) → use it
      2. Perfios AA configured → fetch live
      3. Nothing → ask for CSV upload

    NO MOCK DATA. Real data only.
    """
    business_id = uuid.UUID(payload.business_id)

    business = db.query(Business).filter(
        Business.id == business_id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # ── Check existing data in DB ─────────────────────────────────────────────
    existing_txns = db.query(BankTransaction).filter(
        BankTransaction.business_id == business_id
    ).count()

    if existing_txns > 0:
        account = db.query(BankAccount).filter(
            BankAccount.business_id == business_id
        ).first()

        logger.info(f"Using existing {existing_txns} transactions for {business_id}")

        return {
            "status":              "success",
            "source":              "database",
            "business_id":         str(business_id),
            "transactions_stored": existing_txns,
            "account": {
                "bank_name":           account.bank_name        if account else "Unknown",
                "masked_account":      account.masked_account   if account else "XXXX",
                "avg_monthly_credits": float(account.avg_monthly_credits) if account else 0,
                "avg_monthly_balance": float(account.avg_monthly_balance) if account else 0,
                "bounce_count_12m":    account.bounce_count_12m if account else 0,
            },
            "message": f"{existing_txns} transactions already loaded. Score compute karo.",
            "next_step": "POST /v1/intelligence/score"
        }

    # ── Try Perfios AA if configured ──────────────────────────────────────────
    if AA_CONFIGURED:
        consent = db.query(Consent).filter(
            Consent.business_id == business_id,
            Consent.status == "active"
        ).first()

        if consent:
            try:
                from app.services.perfios_service import fetch_bank_transactions
                financial_data = await fetch_bank_transactions(
                    consent_id=str(consent.aa_consent_id),
                    business_id=str(business_id)
                )

                if financial_data.get("source") != "mock":
                    return await _store_and_return(
                        db, business_id, consent, financial_data
                    )
            except Exception as e:
                logger.error(f"Perfios fetch failed: {e}")

    # ── No data anywhere — ask for CSV ────────────────────────────────────────
    logger.warning(f"No bank data for {business_id} — requesting CSV upload")

    raise HTTPException(
        status_code=400,
        detail={
            "error":           "no_bank_data",
            "message":         "Bank data nahi hai. CSV upload karo.",
            "upload_endpoint": "POST /v1/upload/bank-statement",
            "instructions":    "Apne bank se last 12 months ka statement download karo (CSV/Excel) aur upload karo.",
            "supported":       ["HDFC", "SBI", "ICICI", "Axis", "Kotak"],
        }
    )


async def _store_and_return(
    db: Session,
    business_id: uuid.UUID,
    consent,
    financial_data: dict
) -> dict:
    """Store Perfios data to DB and return summary."""

    # Store account
    account = BankAccount(
        business_id=business_id,
        consent_id=consent.id,
        bank_name=financial_data.get("bank_name", "Unknown"),
        account_type="CURRENT",
        masked_account="XXXX",
        ifsc="",
        avg_monthly_balance=0,
        avg_monthly_credits=financial_data.get("total_credits", 0) / 12,
        avg_monthly_debits=financial_data.get("total_debits", 0) / 12,
        bounce_count_12m=0,
        last_fetched_at=datetime.utcnow()
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    # Store transactions
    for txn in financial_data.get("transactions", []):
        transaction = BankTransaction(
            account_id=business_id,
            business_id=business_id,
            txn_date=datetime.strptime(txn["date"], "%Y-%m-%d"),
            amount=txn["amount"],
            txn_type=txn["type"],
            balance=txn.get("balance", 0),
            narration=txn.get("description", ""),
            category="customer_receipt" if txn["type"] == "CREDIT" else "payment",
            counterparty="",
            is_recurring=False,
            raw_data=txn
        )
        db.add(transaction)

    db.commit()

    total = db.query(BankTransaction).filter(
        BankTransaction.business_id == business_id
    ).count()

    logger.info(f"Stored {total} real transactions for {business_id}")

    return {
        "status":              "success",
        "source":              "perfios_live",
        "business_id":         str(business_id),
        "transactions_stored": total,
        "message":             "Real bank data loaded successfully",
        "next_step":           "POST /v1/intelligence/score"
    }


@router.get("/bank/summary/{business_id}")
def get_bank_summary(business_id: str, db: Session = Depends(get_db)):
    """Bank data summary — no mock, real DB only."""
    bid = uuid.UUID(business_id)

    account = db.query(BankAccount).filter(
        BankAccount.business_id == bid
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail={
                "error":   "no_bank_data",
                "message": "Bank data nahi hai",
                "action":  "POST /v1/upload/bank-statement"
            }
        )

    txn_count = db.query(BankTransaction).filter(
        BankTransaction.business_id == bid
    ).count()

    return {
        "bank_name":           account.bank_name,
        "account_type":        account.account_type,
        "masked_account":      account.masked_account,
        "avg_monthly_balance": float(account.avg_monthly_balance),
        "avg_monthly_credits": float(account.avg_monthly_credits),
        "avg_monthly_debits":  float(account.avg_monthly_debits),
        "bounce_count_12m":    account.bounce_count_12m,
        "total_transactions":  txn_count,
        "last_fetched_at":     account.last_fetched_at,
        "source":              "real_data",
    }