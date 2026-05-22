from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.event_stream import publish_event_sync
from app.agents.pipeline import run_intelligence_pipeline
from app.db.session import get_db
from app.models.invoice import Invoice
from app.services.payment_service import create_payment_link, verify_payment_webhook
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def is_valid_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


class PaymentLinkRequest(BaseModel):
    business_id: str
    invoice_id: str


@router.post("/create-link")
def create_invoice_payment_link(payload: PaymentLinkRequest, db: Session = Depends(get_db)):
    try:
        invoice_id = UUID(payload.invoice_id)
        business_id = UUID(payload.business_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid business_id or invoice_id")

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id,
            Invoice.business_id == business_id,
        )
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Invoice already paid")

    balance_due = float(invoice.total_amount) - float(invoice.paid_amount or 0)
    if balance_due <= 0:
        raise HTTPException(status_code=400, detail="No due amount left")

    result = create_payment_link(
        business_id=payload.business_id,
        amount=balance_due,
        invoice_number=invoice.invoice_number,
        party_name=invoice.party_name,
        description=invoice.description or "Invoice payment",
    )
    invoice.raw_data = {
        **(invoice.raw_data or {}),
        "payment_link_id": result["payment_link_id"],
        "payment_link_url": result["short_url"],
    }
    db.commit()

    logger.info(f"Payment link created for invoice {invoice.invoice_number}")
    return {
        "invoice_number": invoice.invoice_number,
        "party_name": invoice.party_name,
        "amount_due": balance_due,
        "payment_link": result["short_url"],
        "message": f"Share this link with {invoice.party_name} to collect payment",
    }


@router.post("/invoice/{invoice_id}/link")
def get_invoice_payment_link(invoice_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(invoice_id):
        return {
            "invoice_id": invoice_id,
            "payment_link": f"https://rzp.io/l/demo-{invoice_id}",
            "amount_due": 0,
            "status": "demo",
            "note": "Demo link",
        }

    invoice = db.query(Invoice).filter(Invoice.id == UUID(invoice_id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Invoice already paid")

    balance_due = float(invoice.total_amount) - float(invoice.paid_amount or 0)
    result = create_payment_link(
        business_id=str(invoice.business_id),
        amount=balance_due,
        invoice_number=invoice.invoice_number,
        party_name=invoice.party_name,
        description=invoice.description or "Invoice payment",
    )
    invoice.raw_data = {
        **(invoice.raw_data or {}),
        "payment_link_id": result["payment_link_id"],
        "payment_link_url": result["short_url"],
    }
    db.commit()

    return {
        "invoice_id": invoice_id,
        "payment_link": result["short_url"],
        "amount_due": balance_due,
        "status": "created",
    }


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None),
):
    body = await request.json()
    if x_razorpay_signature and not verify_payment_webhook(body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    event = body.get("event")
    logger.info(f"Razorpay webhook received: {event}")

    if event != "payment_link.paid":
        return {"status": "ok"}

    payment_data = body.get("payload", {}).get("payment_link", {}).get("entity", {})
    notes = payment_data.get("notes", {})
    invoice_number = notes.get("invoice_number")
    business_id = notes.get("business_id")
    amount_paid = payment_data.get("amount", 0) / 100

    if not invoice_number or not business_id or not is_valid_uuid(business_id):
        return {"status": "ok"}

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.invoice_number == invoice_number,
            Invoice.business_id == UUID(business_id),
        )
        .first()
    )
    if not invoice:
        return {"status": "ok"}

    existing_paid = float(invoice.paid_amount or 0)
    final_paid = max(existing_paid, amount_paid)
    invoice.paid_amount = final_paid
    invoice.paid_date = date.today()
    invoice.status = "paid" if final_paid >= float(invoice.total_amount) else "partial"
    db.commit()

    logger.info(f"Invoice {invoice_number} marked {invoice.status} with INR {final_paid:,.2f}")

    try:
        publish_event_sync(
            business_id=business_id,
            txn_type="CREDIT",
            amount=amount_paid,
            category="customer_receipt",
            counterparty=invoice.party_name,
        )
    except Exception as exc:
        logger.warning(f"Event stream publish failed (non-fatal): {exc}")

    try:
        run_intelligence_pipeline(business_id, db)
    except Exception as exc:
        logger.warning(f"Score refresh failed after payment (non-fatal): {exc}")

    return {"status": "ok"}


@router.get("/status/{invoice_id}")
def get_payment_status(invoice_id: str, db: Session = Depends(get_db)):
    if not is_valid_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="Invalid invoice_id")

    invoice = db.query(Invoice).filter(Invoice.id == UUID(invoice_id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    payment_link = (invoice.raw_data or {}).get("payment_link_url")
    paid_amount = float(invoice.paid_amount or 0)
    total_amount = float(invoice.total_amount)
    return {
        "invoice_number": invoice.invoice_number,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "balance_due": total_amount - paid_amount,
        "status": invoice.status,
        "payment_link": payment_link,
    }
