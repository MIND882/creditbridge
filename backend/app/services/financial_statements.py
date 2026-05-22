from sqlalchemy.orm import Session
from app.models.bank_data import BankTransaction
from app.models.invoice import Invoice
from app.models.gst_data import GSTFiling
from app.models.risk_score import RiskScore
from app.models.business import Business
from datetime import datetime, date
from uuid import UUID
from collections import defaultdict


def generate_pl_statement(business_id: str, db: Session) -> dict:
    """
    Auto-generate P&L from bank transactions.
    No CA needed — pure data derived.
    """
    bid = UUID(business_id) if isinstance(business_id, str) else business_id

    transactions = db.query(BankTransaction).filter(
        BankTransaction.business_id == bid
    ).order_by(BankTransaction.txn_date).all()

    # Monthly P&L
    monthly = defaultdict(lambda: {
        "revenue": 0, "cogs": 0, "salary": 0,
        "tax": 0, "other_expense": 0, "loan_emi": 0
    })

    for txn in transactions:
        month_key = txn.txn_date.strftime("%Y-%m")
        amount = float(txn.amount)
        category = txn.category or ""

        if txn.txn_type == "CREDIT":
            if category == "customer_receipt":
                monthly[month_key]["revenue"] += amount
        else:
            if category == "supplier_payment":
                monthly[month_key]["cogs"] += amount
            elif category == "salary":
                monthly[month_key]["salary"] += amount
            elif category == "tax_payment":
                monthly[month_key]["tax"] += amount
            elif category == "loan_emi":
                monthly[month_key]["loan_emi"] += amount
            else:
                monthly[month_key]["other_expense"] += amount

    # Build P&L rows
    pl_rows = []
    total_revenue = 0
    total_gross_profit = 0
    total_net_profit = 0

    for month, data in sorted(monthly.items()):
        revenue = data["revenue"]
        cogs = data["cogs"]
        gross_profit = revenue - cogs
        operating_exp = data["salary"] + data["other_expense"]
        ebitda = gross_profit - operating_exp
        net_profit = ebitda - data["tax"] - data["loan_emi"]

        total_revenue += revenue
        total_gross_profit += gross_profit
        total_net_profit += net_profit

        pl_rows.append({
            "month": month,
            "revenue": round(revenue, 2),
            "cogs": round(cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_margin_pct": round((gross_profit / revenue * 100) if revenue > 0 else 0, 1),
            "salary": round(data["salary"], 2),
            "other_expense": round(data["other_expense"], 2),
            "ebitda": round(ebitda, 2),
            "tax": round(data["tax"], 2),
            "loan_emi": round(data["loan_emi"], 2),
            "net_profit": round(net_profit, 2),
            "net_margin_pct": round((net_profit / revenue * 100) if revenue > 0 else 0, 1)
        })

    months_count = len(pl_rows) or 1

    return {
        "period": f"{pl_rows[0]['month']} to {pl_rows[-1]['month']}" if pl_rows else "N/A",
        "months": months_count,
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "avg_monthly_revenue": round(total_revenue / months_count, 2),
            "total_gross_profit": round(total_gross_profit, 2),
            "gross_margin_pct": round((total_gross_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
            "total_net_profit": round(total_net_profit, 2),
            "net_margin_pct": round((total_net_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
            "profitable_months": sum(1 for r in pl_rows if r["net_profit"] > 0)
        },
        "monthly_breakdown": pl_rows
    }


def generate_cash_flow(business_id: str, db: Session) -> dict:
    """Auto-generate Cash Flow Statement."""
    bid = UUID(business_id) if isinstance(business_id, str) else business_id

    transactions = db.query(BankTransaction).filter(
        BankTransaction.business_id == bid
    ).order_by(BankTransaction.txn_date).all()

    monthly_cf = defaultdict(lambda: {"inflow": 0, "outflow": 0, "closing": 0})

    for txn in transactions:
        month_key = txn.txn_date.strftime("%Y-%m")
        amount = float(txn.amount)

        if txn.txn_type == "CREDIT":
            monthly_cf[month_key]["inflow"] += amount
        else:
            monthly_cf[month_key]["outflow"] += amount

        if txn.balance:
            monthly_cf[month_key]["closing"] = float(txn.balance)

    cf_rows = []
    for month, data in sorted(monthly_cf.items()):
        net = data["inflow"] - data["outflow"]
        cf_rows.append({
            "month": month,
            "inflow": round(data["inflow"], 2),
            "outflow": round(data["outflow"], 2),
            "net_cash_flow": round(net, 2),
            "closing_balance": round(data["closing"], 2),
            "is_positive": net > 0
        })

    positive_months = sum(1 for r in cf_rows if r["is_positive"])

    return {
        "period": f"{cf_rows[0]['month']} to {cf_rows[-1]['month']}" if cf_rows else "N/A",
        "summary": {
            "positive_months": positive_months,
            "negative_months": len(cf_rows) - positive_months,
            "avg_monthly_inflow": round(sum(r["inflow"] for r in cf_rows) / len(cf_rows), 2) if cf_rows else 0,
            "avg_monthly_outflow": round(sum(r["outflow"] for r in cf_rows) / len(cf_rows), 2) if cf_rows else 0,
            "avg_net_cash_flow": round(sum(r["net_cash_flow"] for r in cf_rows) / len(cf_rows), 2) if cf_rows else 0,
        },
        "monthly_breakdown": cf_rows
    }


def generate_working_capital_analysis(business_id: str, db: Session) -> dict:
    """Working capital need analysis — loan amount basis."""
    bid = UUID(business_id) if isinstance(business_id, str) else business_id

    # Outstanding receivables
    receivables = db.query(Invoice).filter(
        Invoice.business_id == bid,
        Invoice.invoice_type.in_(["RECEIVABLE", "sales"]),
        Invoice.status.in_(["pending", "overdue", "partial"])
    ).all()

    # Outstanding payables
    payables = db.query(Invoice).filter(
        Invoice.business_id == bid,
        Invoice.invoice_type.in_(["PAYABLE", "purchase"]),
        Invoice.status.in_(["pending", "overdue", "partial"])
    ).all()

    total_receivable = sum(
        float(r.total_amount) - float(r.paid_amount or 0)
        for r in receivables
    )
    total_payable = sum(
        float(p.total_amount) - float(p.paid_amount or 0)
        for p in payables
    )

    working_capital_gap = total_payable - total_receivable
    loan_needed = max(working_capital_gap, 0)

    # DSO — Days Sales Outstanding
    paid_receivables = db.query(Invoice).filter(
        Invoice.business_id == bid,
        Invoice.invoice_type.in_(["RECEIVABLE", "sales"]),
        Invoice.status == "paid",
        Invoice.paid_date.isnot(None)
    ).all()

    dso = 0
    if paid_receivables:
        dso = sum(
            (r.paid_date - r.Invoice_date).days
            for r in paid_receivables
        ) / len(paid_receivables)

    return {
        "outstanding_receivables": round(total_receivable, 2),
        "outstanding_payables": round(total_payable, 2),
        "working_capital_gap": round(working_capital_gap, 2),
        "recommended_loan_amount": round(loan_needed, 2),
        "avg_collection_days": round(dso, 0),
        "receivables_count": len(receivables),
        "payables_count": len(payables),
        "health": "healthy" if working_capital_gap <= 0 else "needs_financing"
    }