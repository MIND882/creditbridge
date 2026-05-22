from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business import Business
from app.models.invoice import Invoice, PaymentReminder
from app.services.notification import notify_invoice_overdue
from app.utils.auth_dependency import get_current_business_id
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class InvoiceType(str, Enum):
    sales = "sales"
    purchase = "purchase"


class InvoiceCreate(BaseModel):
    business_id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date

    party_name: str
    party_gstin: Optional[str] = None
    party_phone: Optional[str] = None

    invoice_type: InvoiceType

    subtotal: Decimal
    gst_rate: Decimal = Decimal("18.00")

    description: Optional[str] = None


class PaymentUpdate(BaseModel):
    paid_amount: Decimal
    paid_date: date


@router.get("")
def get_invoices_for_current_business(
    invoice_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    return list_invoices(
        business_id=UUID(business_id),
        invoice_type=invoice_type,
        status=status,
        db=db,
    )


@router.get("/summary")
def get_summary_for_current_business(
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    return invoice_summary(
        business_id=UUID(business_id),
        db=db,
    )


@router.post("/create")
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if payload.due_date < payload.invoice_date:
        raise HTTPException(status_code=400, detail="Due date cannot be before invoice date")

    if payload.subtotal <= Decimal("0"):
        raise HTTPException(status_code=400, detail="Subtotal must be greater than 0")

    existing_invoice = (
        db.query(Invoice)
        .filter(
            Invoice.business_id == payload.business_id,
            Invoice.invoice_number == payload.invoice_number,
        )
        .first()
    )
    if existing_invoice:
        raise HTTPException(status_code=400, detail="Invoice number already exists for this business")

    gst_amount = payload.subtotal * (payload.gst_rate / Decimal("100"))
    total_amount = payload.subtotal + gst_amount

    invoice = Invoice(
        business_id=payload.business_id,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        party_name=payload.party_name,
        party_gstin=payload.party_gstin,
        party_phone=payload.party_phone,
        invoice_type=payload.invoice_type.value,
        subtotal=payload.subtotal,
        gst_rate=payload.gst_rate,
        gst_amount=gst_amount,
        total_amount=total_amount,
        status="pending",
        paid_amount=Decimal("0.00"),
        description=payload.description,
    )

    try:
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
    except Exception:
        db.rollback()
        logger.exception("Invoice creation failed")
        raise HTTPException(status_code=500, detail="Failed to create invoice")

    logger.info(
        f"Invoice created: {invoice.invoice_number} | INR {float(total_amount):,.2f} | [{invoice.invoice_type}]"
    )

    return {
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "invoice_date": str(invoice.invoice_date),
        "party_name": invoice.party_name,
        "invoice_type": invoice.invoice_type,
        "subtotal": float(invoice.subtotal),
        "gst_amount": float(invoice.gst_amount),
        "total_amount": float(invoice.total_amount),
        "due_date": str(invoice.due_date),
        "status": invoice.status,
    }


@router.get("/list/{business_id}")
def list_invoices(
    business_id: UUID,
    invoice_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    query = db.query(Invoice).filter(Invoice.business_id == business_id)

    if invoice_type:
        query = query.filter(Invoice.invoice_type == invoice_type.lower())
    if status:
        query = query.filter(Invoice.status == status.lower())

    invoices = query.order_by(Invoice.due_date.asc()).all()

    today = date.today()
    updated = False
    for inv in invoices:
        if inv.status == "pending" and inv.due_date < today:
            inv.days_overdue = (today - inv.due_date).days
            inv.status = "overdue"
            updated = True

    if updated:
        db.commit()

    response_data = []
    for inv in invoices:
        paid_amount = float(inv.paid_amount or 0)
        total_amount = float(inv.total_amount or 0)
        balance_due = total_amount - paid_amount

        response_data.append(
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "invoice_date": str(inv.invoice_date),
                "party_name": inv.party_name,
                "invoice_type": inv.invoice_type,
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "balance_due": balance_due,
                "due_date": str(inv.due_date),
                "status": inv.status,
                "days_overdue": inv.days_overdue or 0,
            }
        )

    logger.info(f"Invoices fetched for business: {business_id} | Count: {len(response_data)}")
    return {"total": len(response_data), "invoices": response_data}


@router.post("/{invoice_id}/mark-paid")
def mark_paid(
    invoice_id: UUID,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if payload.paid_amount <= Decimal("0"):
        raise HTTPException(status_code=400, detail="Paid amount must be greater than 0")

    total_amount = Decimal(str(invoice.total_amount))
    existing_paid = Decimal(str(invoice.paid_amount or 0))
    new_total_paid = existing_paid + payload.paid_amount

    if new_total_paid > total_amount:
        raise HTTPException(status_code=400, detail="Paid amount exceeds total invoice amount")

    invoice.paid_amount = new_total_paid
    invoice.paid_date = payload.paid_date
    invoice.status = "paid" if new_total_paid >= total_amount else "partial"

    try:
        db.commit()
        db.refresh(invoice)
    except Exception:
        db.rollback()
        logger.exception("Failed to update invoice payment")
        raise HTTPException(status_code=500, detail="Failed to update payment")

    balance_due = float(total_amount - new_total_paid)
    logger.info(
        f"Payment recorded | Invoice: {invoice.invoice_number} | Paid: INR {float(payload.paid_amount):,.2f} | Status: {invoice.status}"
    )

    return {
        "invoice_id": str(invoice.id),
        "status": invoice.status,
        "paid_amount": float(invoice.paid_amount),
        "balance_due": balance_due,
    }


@router.post("/{invoice_id}/remind")
def send_invoice_reminder(invoice_id: UUID, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    business = db.query(Business).filter(Business.id == invoice.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if invoice.status not in {"overdue", "pending", "partial"}:
        raise HTTPException(status_code=400, detail="Reminder only allowed for unpaid invoices")

    outstanding = float(invoice.total_amount or 0) - float(invoice.paid_amount or 0)
    days = max(0, (date.today() - invoice.due_date).days)

    sent = False
    if business.owner_phone:
        sent = notify_invoice_overdue(
            phone=business.owner_phone,
            business_name=business.business_name,
            party_name=invoice.party_name,
            amount=outstanding,
            days=days,
        )

    reminder = PaymentReminder(
        invoice_id=invoice.id,
        business_id=business.id,
        reminder_type="whatsapp",
        status="sent" if sent else "failed",
        message=f"Reminder sent for invoice {invoice.invoice_number}",
    )
    db.add(reminder)
    db.commit()

    return {
        "invoice_id": str(invoice.id),
        "status": "sent" if sent else "failed",
        "party_name": invoice.party_name,
        "outstanding": outstanding,
        "days_overdue": days,
    }


@router.get("/summary/{business_id}")
def invoice_summary(
    business_id: UUID,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    today = date.today()

    invoices = db.query(Invoice).filter(Invoice.business_id == business_id).all()

    receivables = [i for i in invoices if (i.invoice_type or "").lower() == "sales"]
    payables = [i for i in invoices if (i.invoice_type or "").lower() == "purchase"]

    total_receivable = sum(float(i.total_amount or 0) for i in receivables)
    total_collected = sum(float(i.paid_amount or 0) for i in receivables)
    overdue_receivable = sum(
        float(i.total_amount or 0) - float(i.paid_amount or 0)
        for i in receivables
        if i.due_date < today and i.status != "paid"
    )

    paid_receivables = [i for i in receivables if i.status == "paid" and i.paid_date]
    dso = 0
    if paid_receivables:
        dso = sum((i.paid_date - i.invoice_date).days for i in paid_receivables) / len(paid_receivables)

    total_payable = sum(float(i.total_amount or 0) for i in payables)
    overdue_payable = sum(
        float(i.total_amount or 0) - float(i.paid_amount or 0)
        for i in payables
        if i.due_date < today and i.status != "paid"
    )

    buyer_totals: Dict[str, float] = {}
    for inv in receivables:
        buyer_totals[inv.party_name] = buyer_totals.get(inv.party_name, 0) + float(inv.total_amount or 0)

    top_buyers = sorted(buyer_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    invoice_score = _compute_invoice_score(
        collected=total_collected,
        total=total_receivable,
        dso=dso,
        overdue=overdue_receivable,
    )

    logger.info(f"Invoice summary generated | Business: {business_id} | Score: {invoice_score}")

    return {
        "receivables": {
            "total_invoiced": total_receivable,
            "total_collected": total_collected,
            "overdue_amount": overdue_receivable,
            "collection_rate": round((total_collected / total_receivable) * 100, 1) if total_receivable > 0 else 0,
            "avg_collection_days": round(dso, 0),
            "total_invoices": len(receivables),
        },
        "payables": {
            "total_payable": total_payable,
            "overdue_amount": overdue_payable,
            "total_invoices": len(payables),
        },
        "top_buyers": [{"name": name, "amount": amount} for name, amount in top_buyers],
        "invoice_score": invoice_score,
    }


def _compute_invoice_score(collected: float, total: float, dso: float, overdue: float) -> int:
    if total == 0:
        return 50

    collection_rate = collected / total
    dso_score = max(0, 100 - dso)
    collection_score = collection_rate * 100
    overdue_penalty = min(30, (overdue / total) * 100)

    score = (collection_score * 0.5) + (dso_score * 0.3) - overdue_penalty
    return max(0, min(100, int(score)))
