from sqlalchemy.orm import Session
from app.models.bank_data import BankAccount, BankTransaction
from app.agents.state import AgentState
from app.utils.logger import get_logger
from uuid import UUID

logger = get_logger(__name__)

def bank_analyzer_node(state: AgentState, db: Session) -> AgentState:
    """Analyzes bank transactions and produces risk signals."""
    
    bid = state["business_id"]
    business_id = bid if isinstance(bid, UUID) else UUID(str(bid))
    logger.info(f"[BankAnalyzer] Running for {business_id}")

    account = db.query(BankAccount).filter(
        BankAccount.business_id == business_id
    ).first()

    if not account:
        return {**state, "error": "No bank data found"}

    transactions = db.query(BankTransaction).filter(
        BankTransaction.business_id == business_id
    ).all()

    if not transactions:
        return {**state, "error": "No transactions found"}

    # Core signals
    credits = [t for t in transactions if t.txn_type == "CREDIT"]
    debits  = [t for t in transactions if t.txn_type == "DEBIT"]
    bounces = [t for t in transactions if t.category == "bounce"]

    total_credits = sum(float(t.amount) for t in credits)
    total_debits  = sum(float(t.amount) for t in debits)

    # FIX: None-safe — agar DB mein None hai toh transactions se calculate karo
    if account.avg_monthly_credits is not None:
        avg_monthly_revenue = float(account.avg_monthly_credits)
    else:
        # Calculate from actual transactions
        monthly_map = {}
        for t in credits:
            mk = t.txn_date.strftime("%Y-%m")
            monthly_map[mk] = monthly_map.get(mk, 0) + float(t.amount)
        avg_monthly_revenue = (
            sum(monthly_map.values()) / len(monthly_map)
            if monthly_map else 0.0
        )
        # Save back to account
        account.avg_monthly_credits = avg_monthly_revenue
        db.commit()

    if account.avg_monthly_balance is not None:
        avg_monthly_balance = float(account.avg_monthly_balance)
    else:
        # Estimate from transaction balances
        balances = [float(t.balance) for t in transactions if t.balance is not None]
        avg_monthly_balance = sum(balances) / len(balances) if balances else total_credits * 0.3
        # Save back
        account.avg_monthly_balance = avg_monthly_balance
        db.commit()

    bounce_rate = len(bounces) / max(len(transactions), 1)

    # Customer concentration risk
    from collections import Counter
    customer_txns = [t.counterparty for t in credits if t.counterparty]
    top_customers = Counter(customer_txns).most_common(3)
    top_3_revenue_pct = min(len(top_customers) * 25, 75)

    # Cash flow consistency (month over month)
    monthly_credits = {}
    for t in credits:
        month_key = t.txn_date.strftime("%Y-%m")
        monthly_credits[month_key] = monthly_credits.get(month_key, 0) + float(t.amount)

    values = list(monthly_credits.values())
    if len(values) > 1:
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        consistency_score = max(0, 100 - (variance ** 0.5 / avg * 100))
    else:
        consistency_score = 50

    bank_signals = {
        "avg_monthly_revenue":        avg_monthly_revenue,
        "avg_monthly_balance":        avg_monthly_balance,
        "total_credits_12m":          total_credits,
        "total_debits_12m":           total_debits,
        "bounce_count":               len(bounces),
        "bounce_rate":                round(bounce_rate, 4),
        "consistency_score":          round(consistency_score, 2),
        "top_customer_concentration": top_3_revenue_pct,
        "months_of_data":             len(monthly_credits),
        "unique_customers":           len(set(customer_txns)),
    }

    logger.info(f"[BankAnalyzer] Signals: {bank_signals}")
    return {**state, "bank_signals": bank_signals}