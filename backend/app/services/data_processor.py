"""
Data Processor
Converts raw bank transactions + GST data into intelligence signals
"""
from typing import Optional
from app.utils.logger import get_logger
from collections import defaultdict
import datetime

logger = get_logger(__name__)


def process_bank_transactions(transactions: list) -> dict:
    """
    Raw transactions → monthly summary → signals
    """
    if not transactions:
        return _empty_summary()

    monthly: dict = defaultdict(lambda: {"credits": 0.0, "debits": 0.0, "count": 0})

    for txn in transactions:
        date_str = txn.get("date", "")[:7]  # YYYY-MM
        amount   = float(txn.get("amount", 0))
        if txn.get("type") == "CREDIT":
            monthly[date_str]["credits"] += amount
        else:
            monthly[date_str]["debits"]  += amount
        monthly[date_str]["count"] += 1

    months       = sorted(monthly.keys())
    credits_list = [monthly[m]["credits"] for m in months]
    debits_list  = [monthly[m]["debits"]  for m in months]

    avg_credits  = sum(credits_list) / len(credits_list) if credits_list else 0
    avg_debits   = sum(debits_list)  / len(debits_list)  if debits_list  else 0

    # Bounce detection — months with credits < debits
    bounce_months = sum(1 for m in months if monthly[m]["credits"] < monthly[m]["debits"])

    # Revenue trend — last 3 vs first 3 months
    trend = "stable"
    if len(credits_list) >= 6:
        recent_avg = sum(credits_list[-3:]) / 3
        older_avg  = sum(credits_list[:3])  / 3
        if older_avg > 0:
            growth = (recent_avg - older_avg) / older_avg
            trend  = "growing" if growth > 0.1 else "declining" if growth < -0.1 else "stable"

    return {
        "monthly_summary":   dict(monthly),
        "avg_monthly_credit": round(avg_credits, 0),
        "avg_monthly_debit":  round(avg_debits, 0),
        "total_credits":      sum(credits_list),
        "total_debits":       sum(debits_list),
        "bounce_months":      bounce_months,
        "revenue_trend":      trend,
        "months_analyzed":    len(months),
        "utilization_ratio":  round(avg_debits / avg_credits, 2) if avg_credits > 0 else 1.0,
    }


def process_gst_data(gst_data: dict) -> dict:
    """GST returns → compliance + revenue signals"""
    filings  = gst_data.get("filings", [])
    if not filings:
        return {"gst_compliance_score": 0, "avg_monthly_gst_turnover": 0, "filing_gaps": 0}

    turnovers = [f.get("turnover", 0) for f in filings]
    avg_to    = sum(turnovers) / len(turnovers) if turnovers else 0

    return {
        "gst_compliance_score":    gst_data.get("compliance", 0),
        "avg_monthly_gst_turnover": round(avg_to, 0),
        "total_gst_turnover":       sum(turnovers),
        "filing_count":             len(filings),
        "filing_gaps":              max(0, 12 - len(filings)),
    }


def combine_signals(bank_signals: dict, gst_signals: dict) -> dict:
    """Combine bank + GST into unified credit signals"""
    bank_revenue = bank_signals.get("avg_monthly_credit", 0)
    gst_revenue  = gst_signals.get("avg_monthly_gst_turnover", 0)

    # Revenue consistency check
    revenue_match = True
    if bank_revenue > 0 and gst_revenue > 0:
        ratio = min(bank_revenue, gst_revenue) / max(bank_revenue, gst_revenue)
        revenue_match = ratio > 0.6  # Within 40% of each other

    working_capital = bank_revenue * 0.3  # ~1 month working capital buffer

    return {
        "avg_monthly_revenue":  max(bank_revenue, gst_revenue),
        "revenue_consistency":  revenue_match,
        "working_capital_est":  round(working_capital, 0),
        "bounce_risk":          bank_signals.get("bounce_months", 0) > 2,
        "revenue_trend":        bank_signals.get("revenue_trend", "stable"),
        "gst_compliance":       gst_signals.get("gst_compliance_score", 0),
        "recommended_limit":    round(max(bank_revenue, gst_revenue) * 3, 0),
    }


def _empty_summary() -> dict:
    return {
        "monthly_summary": {}, "avg_monthly_credit": 0,
        "avg_monthly_debit": 0, "total_credits": 0, "total_debits": 0,
        "bounce_months": 0, "revenue_trend": "unknown", "months_analyzed": 0,
        "utilization_ratio": 0,
    }