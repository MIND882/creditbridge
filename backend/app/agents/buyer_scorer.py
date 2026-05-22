from sqlalchemy.orm import Session
from app.models.bank_data import BankTransaction
from app.models.invoice import Invoice
from app.agents.state import AgentState
from app.utils.logger import get_logger
from uuid import UUID
from collections import defaultdict
from datetime import datetime, timedelta

logger = get_logger(__name__)


def buyer_scorer_node(state: AgentState, db: Session) -> AgentState:
    """
    Analyzes buyer payment behavior.
    Answers: Who pays on time? Who delays? Who is risky?
    This is critical for lender trust — buyer quality = MSME quality.
    """
    bid = state["business_id"]
    business_id = bid if isinstance(bid, UUID) else UUID(str(bid))

    logger.info(f"[BuyerScorer] Running for {business_id}")

    # Get all receivable invoices
    invoices = db.query(Invoice).filter(
        Invoice.business_id == business_id,
        Invoice.invoice_type.in_(["RECEIVABLE", "sales"])
    ).all()

    # Get credit transactions — customer payments
    credits = db.query(BankTransaction).filter(
        BankTransaction.business_id == business_id,
        BankTransaction.txn_type == "CREDIT",
        BankTransaction.category == "customer_receipt"
    ).all()

    # Build buyer profiles from invoices
    buyer_profiles = defaultdict(lambda: {
        "name": "",
        "total_invoiced": 0,
        "total_paid": 0,
        "invoice_count": 0,
        "paid_count": 0,
        "overdue_count": 0,
        "avg_days_to_pay": 0,
        "days_list": [],
        "last_payment": None,
        "reliability_score": 0
    })

    today = datetime.utcnow().date()

    for inv in invoices:
        name = inv.party_name or "Unknown"
        buyer_profiles[name]["name"] = name
        buyer_profiles[name]["total_invoiced"] += float(inv.total_amount)
        buyer_profiles[name]["total_paid"] += float(inv.paid_amount or 0)
        buyer_profiles[name]["invoice_count"] += 1

        if inv.status == "paid" and inv.paid_date and inv.invoice_date:
            days = (inv.paid_date - inv.invoice_date).days
            buyer_profiles[name]["days_list"].append(days)
            buyer_profiles[name]["paid_count"] += 1
            if inv.paid_date > (buyer_profiles[name]["last_payment"] or inv.paid_date):
                buyer_profiles[name]["last_payment"] = inv.paid_date

        if inv.status == "overdue":
            buyer_profiles[name]["overdue_count"] += 1

    # Also analyze from bank transactions
    for txn in credits:
        if txn.counterparty and txn.counterparty not in buyer_profiles:
            buyer_profiles[txn.counterparty]["name"] = txn.counterparty

    # Compute reliability scores
    buyer_scores = []
    total_revenue_concentration = 0

    for name, profile in buyer_profiles.items():
        days_list = profile["days_list"]
        invoice_count = profile["invoice_count"]
        paid_count = profile["paid_count"]
        overdue_count = profile["overdue_count"]
        total_invoiced = profile["total_invoiced"]

        # Payment speed score (0-40)
        if days_list:
            avg_days = sum(days_list) / len(days_list)
            profile["avg_days_to_pay"] = round(avg_days, 1)
            if avg_days <= 15:
                speed_score = 40
            elif avg_days <= 30:
                speed_score = 30
            elif avg_days <= 45:
                speed_score = 20
            elif avg_days <= 60:
                speed_score = 10
            else:
                speed_score = 0
        else:
            avg_days = 0
            speed_score = 20  # Neutral — no data

        # Payment consistency score (0-35)
        if invoice_count > 0:
            payment_rate = paid_count / invoice_count
            consistency_score = int(payment_rate * 35)
        else:
            consistency_score = 17

        # Overdue penalty (0-25)
        if invoice_count > 0:
            overdue_rate = overdue_count / invoice_count
            overdue_score = int((1 - overdue_rate) * 25)
        else:
            overdue_score = 20

        reliability = speed_score + consistency_score + overdue_score

        profile["reliability_score"] = reliability
        total_revenue_concentration += total_invoiced

        buyer_scores.append({
            "name": name,
            "total_invoiced": round(total_invoiced, 2),
            "total_paid": round(profile["total_paid"], 2),
            "collection_rate_pct": round(
                (profile["total_paid"] / total_invoiced * 100) if total_invoiced > 0 else 0, 1
            ),
            "invoice_count": invoice_count,
            "paid_on_time": paid_count,
            "overdue_count": overdue_count,
            "avg_days_to_pay": round(avg_days, 1),
            "reliability_score": reliability,
            "reliability_grade": (
                "EXCELLENT" if reliability >= 80 else
                "GOOD" if reliability >= 60 else
                "FAIR" if reliability >= 40 else
                "POOR"
            ),
            "last_payment": str(profile["last_payment"]) if profile["last_payment"] else None
        })

    # Sort by total invoiced
    buyer_scores.sort(key=lambda x: x["total_invoiced"], reverse=True)

    # Concentration risk
    top_3_revenue = sum(b["total_invoiced"] for b in buyer_scores[:3])
    concentration_pct = (
        top_3_revenue / total_revenue_concentration * 100
        if total_revenue_concentration > 0 else 0
    )

    # Overall buyer network score
    if buyer_scores:
        avg_reliability = sum(b["reliability_score"] for b in buyer_scores) / len(buyer_scores)
        excellent_buyers = sum(1 for b in buyer_scores if b["reliability_score"] >= 80)
        poor_buyers = sum(1 for b in buyer_scores if b["reliability_score"] < 40)
    else:
        avg_reliability = 50
        excellent_buyers = 0
        poor_buyers = 0

    buyer_signals = {
        "total_buyers": len(buyer_scores),
        "avg_buyer_reliability": round(avg_reliability, 1),
        "excellent_buyers": excellent_buyers,
        "poor_buyers": poor_buyers,
        "top_3_concentration_pct": round(concentration_pct, 1),
        "concentration_risk": concentration_pct > 70,
        "top_buyers": buyer_scores[:5],
        "all_buyers": buyer_scores
    }

    logger.info(
        f"[BuyerScorer] {len(buyer_scores)} buyers, "
        f"avg reliability: {avg_reliability:.0f}, "
        f"concentration: {concentration_pct:.0f}%"
    )

    return {**state, "buyer_signals": buyer_signals}