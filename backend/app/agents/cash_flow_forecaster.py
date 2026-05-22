from sqlalchemy.orm import Session
from app.models.bank_data import BankTransaction
from app.models.invoice import Invoice
from app.agents.state import AgentState
from app.utils.logger import get_logger
from uuid import UUID
from collections import defaultdict
from datetime import datetime, timedelta, date
import statistics

logger = get_logger(__name__)


def cash_flow_forecaster_node(state: AgentState, db: Session) -> AgentState:
    """
    Predicts cash flow for next 30, 60, 90 days.
    Uses historical patterns + outstanding invoices.
    This is what makes lenders pay ₹1Cr/year — predictive, not just historical.
    """
    bid = state["business_id"]
    business_id = bid if isinstance(bid, UUID) else UUID(str(bid))

    logger.info(f"[CashFlowForecaster] Running for {business_id}")

    # Get last 12 months transactions
    cutoff = datetime.utcnow() - timedelta(days=365)
    transactions = db.query(BankTransaction).filter(
        BankTransaction.business_id == business_id,
        BankTransaction.txn_date >= cutoff
    ).order_by(BankTransaction.txn_date).all()

    # Monthly actuals
    monthly_inflow = defaultdict(float)
    monthly_outflow = defaultdict(float)

    for txn in transactions:
        month_key = txn.txn_date.strftime("%Y-%m")
        amount = float(txn.amount)
        if txn.txn_type == "CREDIT":
            monthly_inflow[month_key] += amount
        else:
            monthly_outflow[month_key] += amount

    inflow_values = list(monthly_inflow.values())
    outflow_values = list(monthly_outflow.values())

    # Statistical baseline
    if len(inflow_values) >= 3:
        avg_inflow = statistics.mean(inflow_values)
        avg_outflow = statistics.mean(outflow_values) if outflow_values else avg_inflow * 0.4

        # Trend — last 3 months vs previous
        if len(inflow_values) >= 6:
            recent_avg = statistics.mean(inflow_values[-3:])
            older_avg = statistics.mean(inflow_values[-6:-3])
            trend_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            trend_pct = 0

        # Seasonality — same month last year
        current_month = datetime.utcnow().month
        seasonal_months = [
            k for k in monthly_inflow.keys()
            if int(k.split("-")[1]) == current_month
        ]
        seasonal_factor = 1.0
        if seasonal_months:
            seasonal_avg = statistics.mean([monthly_inflow[m] for m in seasonal_months])
            seasonal_factor = seasonal_avg / avg_inflow if avg_inflow > 0 else 1.0
            seasonal_factor = max(0.7, min(1.5, seasonal_factor))

        # Variance for confidence
        if len(inflow_values) >= 3:
            std_dev = statistics.stdev(inflow_values)
            cv = std_dev / avg_inflow if avg_inflow > 0 else 0
            confidence = max(0.5, min(0.95, 1 - cv))
        else:
            confidence = 0.6

    else:
        avg_inflow = inflow_values[0] if inflow_values else 4000000
        avg_outflow = outflow_values[0] if outflow_values else avg_inflow * 0.4
        trend_pct = 0
        seasonal_factor = 1.0
        confidence = 0.5

    # Outstanding invoices — known future inflows
    outstanding = db.query(Invoice).filter(
        Invoice.business_id == business_id,
        Invoice.invoice_type.in_(["RECEIVABLE", "sales"]),
        Invoice.status.in_(["pending", "partial", "overdue"])
    ).all()

    today = date.today()
    known_inflow_30 = 0
    known_inflow_60 = 0
    known_inflow_90 = 0

    for inv in outstanding:
        balance = float(inv.total_amount) - float(inv.paid_amount or 0)
        days_due = (inv.due_date - today).days if inv.due_date else 30

        if days_due <= 30:
            known_inflow_30 += balance * 0.85   # 85% collection probability
        elif days_due <= 60:
            known_inflow_60 += balance * 0.80
        elif days_due <= 90:
            known_inflow_90 += balance * 0.75

    # Apply trend
    trend_multiplier = 1 + (trend_pct / 100 / 12)  # Monthly trend

    # Forecast
    base_monthly = avg_inflow * seasonal_factor * trend_multiplier
    base_outflow = avg_outflow * trend_multiplier

    forecast_30 = {
        "period": "Next 30 days",
        "expected_inflow": round(base_monthly * 0.8 + known_inflow_30, 2),
        "known_receivables": round(known_inflow_30, 2),
        "statistical_inflow": round(base_monthly * 0.8, 2),
        "expected_outflow": round(base_outflow * 0.8, 2),
        "net_cash_flow": round((base_monthly * 0.8 + known_inflow_30) - (base_outflow * 0.8), 2),
        "confidence": round(confidence * 0.95, 2)
    }

    forecast_60 = {
        "period": "Next 60 days",
        "expected_inflow": round(base_monthly * 1.7 + known_inflow_30 + known_inflow_60, 2),
        "known_receivables": round(known_inflow_30 + known_inflow_60, 2),
        "statistical_inflow": round(base_monthly * 1.7, 2),
        "expected_outflow": round(base_outflow * 1.7, 2),
        "net_cash_flow": round((base_monthly * 1.7 + known_inflow_30 + known_inflow_60) - (base_outflow * 1.7), 2),
        "confidence": round(confidence * 0.85, 2)
    }

    forecast_90 = {
        "period": "Next 90 days",
        "expected_inflow": round(base_monthly * 2.6 + known_inflow_30 + known_inflow_60 + known_inflow_90, 2),
        "known_receivables": round(known_inflow_30 + known_inflow_60 + known_inflow_90, 2),
        "statistical_inflow": round(base_monthly * 2.6, 2),
        "expected_outflow": round(base_outflow * 2.6, 2),
        "net_cash_flow": round(
            (base_monthly * 2.6 + known_inflow_30 + known_inflow_60 + known_inflow_90) - (base_outflow * 2.6), 2
        ),
        "confidence": round(confidence * 0.75, 2)
    }

    # Working capital need assessment
    min_balance_needed = base_outflow * 1.5   # 1.5 months buffer
    current_avg_balance = (
        statistics.mean([float(t.balance) for t in transactions[-30:] if t.balance])
        if transactions else 0
    )

    working_capital_gap = max(0, min_balance_needed - current_avg_balance)

    # Stress scenario — what if top buyer delays?
    stress_inflow = base_monthly * 0.6  # 40% revenue drop
    stress_net = stress_inflow - base_outflow
    stressed = stress_net < 0

    forecast_signals = {
        "historical_avg_monthly_inflow": round(avg_inflow, 2),
        "historical_avg_monthly_outflow": round(avg_outflow, 2),
        "trend_pct": round(trend_pct, 1),
        "seasonal_factor": round(seasonal_factor, 2),
        "forecast_30": forecast_30,
        "forecast_60": forecast_60,
        "forecast_90": forecast_90,
        "working_capital_gap": round(working_capital_gap, 2),
        "needs_working_capital": working_capital_gap > 0,
        "stress_test": {
            "scenario": "40% revenue drop",
            "net_cash_flow": round(stress_net, 2),
            "at_risk": stressed,
            "months_runway": round(
                current_avg_balance / abs(stress_net) if stressed and stress_net != 0 else 99, 1
            )
        },
        "overall_outlook": (
            "STRONG" if forecast_90["net_cash_flow"] > avg_inflow else
            "STABLE" if forecast_90["net_cash_flow"] > 0 else
            "CAUTION"
        )
    }

    logger.info(
        f"[CashFlowForecaster] 30d: Rs.{forecast_30['net_cash_flow']/100000:.1f}L | "
        f"90d: Rs.{forecast_90['net_cash_flow']/100000:.1f}L | "
        f"Outlook: {forecast_signals['overall_outlook']}"
    )

    return {**state, "forecast_signals": forecast_signals}