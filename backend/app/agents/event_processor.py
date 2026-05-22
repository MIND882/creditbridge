from sqlalchemy.orm import Session
from app.models.bank_data import BankTransaction
from app.models.invoice import Invoice
from app.models.risk_score import RiskScore
from app.models.business import Business
from app.utils.logger import get_logger
from app.agents.pipeline import run_intelligence_pipeline
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict

logger = get_logger(__name__)


class TransactionEvent:
    """Represents a new transaction event."""
    def __init__(self, business_id: str, txn_type: str, amount: float,
                 category: str, counterparty: str = None):
        self.business_id = business_id
        self.txn_type = txn_type
        self.amount = amount
        self.category = category
        self.counterparty = counterparty
        self.timestamp = datetime.utcnow()


def process_transaction_event(event: TransactionEvent, db: Session) -> dict:
    """
    Called every time a new transaction enters the system.
    This is the real-time intelligence layer.

    Flow:
    New transaction → classify → update signals → refresh score → alert lender
    """
    bid = UUID(event.business_id) if isinstance(event.business_id, str) else event.business_id
    logger.info(f"[EventProcessor] New {event.txn_type} ₹{event.amount:,.0f} for {bid}")

    results = {
        "business_id": str(bid),
        "event_type": event.txn_type,
        "amount": event.amount,
        "category": event.category,
        "alerts": [],
        "score_updated": False,
        "old_score": None,
        "new_score": None
    }

    # Get current score
    current_score = db.query(RiskScore).filter(
        RiskScore.business_id == bid
    ).first()
    if current_score:
        results["old_score"] = current_score.score

    # Step 1: Classify and process event
    alerts = []

    if event.txn_type == "CREDIT":
        alerts.extend(_process_credit_event(event, bid, db))
    else:
        alerts.extend(_process_debit_event(event, bid, db))

    # Step 2: Check for risk signals
    alerts.extend(_check_risk_signals(bid, db))

    # Step 3: Auto-match invoice if possible
    invoice_matched = _match_invoice(event, bid, db)
    if invoice_matched:
        results["invoice_matched"] = invoice_matched

    # Step 4: Refresh score
    try:
        new_score_data = run_intelligence_pipeline(str(bid), db)
        if new_score_data and "score" in new_score_data:
            results["new_score"] = new_score_data["score"]
            results["score_updated"] = True

            if results["old_score"] and results["new_score"]:
                diff = results["new_score"] - results["old_score"]
                if abs(diff) >= 5:
                    direction = "up" if diff > 0 else "down"
                    alerts.append({
                        "type": "score_change",
                        "severity": "info",
                        "message": f"Credit score {direction} by {abs(diff)} points: {results['old_score']} → {results['new_score']}",
                        "action": "Monitor"
                    })
    except Exception as e:
        logger.error(f"[EventProcessor] Score refresh failed: {e}")

    results["alerts"] = alerts
    logger.info(f"[EventProcessor] Done — {len(alerts)} alerts, score: {results.get('old_score')} → {results.get('new_score')}")
    return results


def _process_credit_event(event: TransactionEvent, bid: UUID, db: Session) -> list:
    """Process incoming payment — customer paid."""
    alerts = []

    if event.category == "customer_receipt":
        # Check if this is a large payment
        avg_txn = _get_avg_transaction(bid, "CREDIT", db)
        if avg_txn and event.amount > avg_txn * 2:
            alerts.append({
                "type": "large_payment",
                "severity": "positive",
                "message": f"Large payment received ₹{event.amount/100000:.1f}L from {event.counterparty or 'customer'} — 2x above average",
                "action": "None required"
            })

    return alerts


def _process_debit_event(event: TransactionEvent, bid: UUID, db: Session) -> list:
    """Process outgoing payment — MSME paid someone."""
    alerts = []

    if event.category == "bounce":
        alerts.append({
            "type": "bounce_detected",
            "severity": "critical",
            "message": f"Cheque bounce detected — ₹{event.amount/100000:.1f}L. Credit score will be impacted.",
            "action": "Immediate review required"
        })

    elif event.category == "loan_emi":
        # Check if EMI is being paid — good sign
        alerts.append({
            "type": "emi_paid",
            "severity": "positive",
            "message": f"Loan EMI paid ₹{event.amount/100000:.1f}L — consistent repayment",
            "action": "None"
        })

    return alerts


def _check_risk_signals(bid: UUID, db: Session) -> list:
    """Check for risk patterns after each transaction."""
    alerts = []
    cutoff = datetime.utcnow() - timedelta(days=30)

    recent_txns = db.query(BankTransaction).filter(
        BankTransaction.business_id == bid,
        BankTransaction.txn_date >= cutoff
    ).all()

    if not recent_txns:
        return alerts

    # Check bounce rate
    bounces = [t for t in recent_txns if t.category == "bounce"]
    if len(bounces) >= 2:
        alerts.append({
            "type": "high_bounce_rate",
            "severity": "warning",
            "message": f"{len(bounces)} bounces in last 30 days — credit risk increasing",
            "action": "Review loan limits"
        })

    # Check revenue trend
    credits = [float(t.amount) for t in recent_txns if t.txn_type == "CREDIT"]
    if credits:
        recent_avg = sum(credits) / len(credits)
        prev_cutoff = datetime.utcnow() - timedelta(days=60)
        prev_txns = db.query(BankTransaction).filter(
            BankTransaction.business_id == bid,
            BankTransaction.txn_date >= prev_cutoff,
            BankTransaction.txn_date < cutoff,
            BankTransaction.txn_type == "CREDIT"
        ).all()

        if prev_txns:
            prev_avg = sum(float(t.amount) for t in prev_txns) / len(prev_txns)
            drop_pct = ((prev_avg - recent_avg) / prev_avg * 100) if prev_avg > 0 else 0

            if drop_pct > 30:
                alerts.append({
                    "type": "revenue_drop",
                    "severity": "warning",
                    "message": f"Revenue dropped {drop_pct:.0f}% vs last month — monitor closely",
                    "action": "Contact business owner"
                })

    # Check overdue invoices
    overdue = db.query(Invoice).filter(
        Invoice.business_id == bid,
        Invoice.status == "overdue"
    ).count()

    if overdue >= 3:
        alerts.append({
            "type": "multiple_overdue",
            "severity": "warning",
            "message": f"{overdue} overdue invoices — collection efficiency declining",
            "action": "Review working capital"
        })

    return alerts


def _match_invoice(event: TransactionEvent, bid: UUID, db: Session) -> dict | None:
    """Try to auto-match transaction to an invoice."""
    if event.txn_type != "CREDIT" or not event.counterparty:
        return None

    # Find pending invoice from same party
    invoice = db.query(Invoice).filter(
        Invoice.business_id == bid,
        Invoice.party_name.ilike(f"%{event.counterparty[:10]}%"),
        Invoice.status.in_(["pending", "partial"])
    ).first()

    if invoice:
        balance = float(invoice.total_amount) - float(invoice.paid_amount or 0)
        if abs(event.amount - balance) < balance * 0.05:  # 5% tolerance
            from datetime import date
            invoice.paid_amount = float(invoice.total_amount)
            invoice.paid_date = date.today()
            invoice.status = "paid"
            db.commit()
            logger.info(f"[EventProcessor] Auto-matched invoice {invoice.Invoice_number}")
            return {
                "invoice_number": invoice.Invoice_number,
                "party": invoice.party_name,
                "amount": float(invoice.total_amount)
            }

    return None


def _get_avg_transaction(bid: UUID, txn_type: str, db: Session) -> float | None:
    """Get average transaction amount for comparison."""
    cutoff = datetime.utcnow() - timedelta(days=90)
    txns = db.query(BankTransaction).filter(
        BankTransaction.business_id == bid,
        BankTransaction.txn_type == txn_type,
        BankTransaction.txn_date >= cutoff
    ).all()

    if not txns:
        return None
    return sum(float(t.amount) for t in txns) / len(txns)


def get_business_alerts(business_id: str, db: Session, days: int = 30) -> list:
    """
    Get all active alerts for a business.
    Used by lender dashboard for real-time monitoring.
    """
    bid = UUID(business_id) if isinstance(business_id, str) else business_id
    alerts = []
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Recent transactions
    recent = db.query(BankTransaction).filter(
        BankTransaction.business_id == bid,
        BankTransaction.txn_date >= cutoff
    ).all()

    # Bounce check
    bounces = [t for t in recent if t.category == "bounce"]
    if bounces:
        alerts.append({
            "type": "bounce",
            "severity": "critical",
            "message": f"{len(bounces)} bounce(s) in last {days} days",
            "count": len(bounces),
            "action": "Immediate review"
        })

    # Revenue trend
    monthly = defaultdict(float)
    for t in recent:
        if t.txn_type == "CREDIT":
            monthly[t.txn_date.strftime("%Y-%m")] += float(t.amount)

    if len(monthly) >= 2:
        months = sorted(monthly.keys())
        if monthly[months[-1]] < monthly[months[-2]] * 0.7:
            drop = (1 - monthly[months[-1]] / monthly[months[-2]]) * 100
            alerts.append({
                "type": "revenue_drop",
                "severity": "warning",
                "message": f"Revenue down {drop:.0f}% this month vs last month",
                "action": "Contact business"
            })

    # Overdue invoices
    overdue_invoices = db.query(Invoice).filter(
        Invoice.business_id == bid,
        Invoice.status == "overdue"
    ).all()

    if overdue_invoices:
        overdue_amount = sum(float(i.total_amount) - float(i.paid_amount or 0) for i in overdue_invoices)
        alerts.append({
            "type": "overdue_invoices",
            "severity": "warning",
            "message": f"{len(overdue_invoices)} overdue invoice(s) — ₹{overdue_amount/100000:.1f}L outstanding",
            "action": "Review collection"
        })

    # Score check
    score = db.query(RiskScore).filter(RiskScore.business_id == bid).first()
    if score and score.score < 650:
        alerts.append({
            "type": "low_score",
            "severity": "critical",
            "message": f"Credit score {score.score} — below safe threshold (650)",
            "action": "Review loan exposure"
        })

    return alerts