from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from app.models.gst_data import GSTFiling
from app.models.bank_data import BankTransaction
from app.agents.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def gst_analyzer_node(state: AgentState, db: Session) -> AgentState:
    """
    Analyze GST compliance + revenue consistency

    Core lender signal:
    GST declared turnover vs actual bank credits

    High mismatch = underwriting red flag
    """

    # state should already contain validated UUID
    business_id = state["business_id"]

    logger.info(f"[GSTAnalyzer] Running for business: {business_id}")

    # --------------------------------------------------
    # 1. Fetch GST filings
    # --------------------------------------------------

    filings = (
        db.query(GSTFiling)
        .filter(GSTFiling.business_id == business_id)
        .order_by(GSTFiling.tax_period.desc())
        .all()
    )

    # IMPORTANT:
    # Never silently use mock data in production
    if not filings:
        logger.warning(
            f"[GSTAnalyzer] No GST filings found for business: {business_id}"
        )

        return {
            **state,
            "gst_signals": {
                "total_periods": 0,
                "filing_rate": 0,
                "filed_on_time": 0,
                "avg_monthly_turnover": 0,
                "b2b_ratio": 0,
                "revenue_match_ratio": 0,
                "compliance_score": 40,
                "risk_band": "no_data",
                "has_real_data": False
            }
        }

    # --------------------------------------------------
    # 2. GST Filing Analysis
    # --------------------------------------------------

    total_periods = len(filings)

    filed_on_time = sum(
        1 for filing in filings
        if filing.filed_on_time
    )

    filing_rate = (
        filed_on_time / total_periods
        if total_periods > 0 else 0
    )

    total_turnover = sum(
        Decimal(str(f.taxable_turnover or 0))
        for f in filings
    )

    avg_monthly_gst_turnover = (
        total_turnover / Decimal(str(total_periods))
        if total_periods > 0 else Decimal("0")
    )

    # Higher B2B ratio = stronger formal business
    total_b2b = sum(
        Decimal(str(f.b2b_turnover or 0))
        for f in filings
    )

    b2b_ratio = (
        float(total_b2b / total_turnover)
        if total_turnover > 0 else 0
    )

    # --------------------------------------------------
    # 3. Bank Credits Analysis
    # --------------------------------------------------

    total_bank_credits = (
        db.query(
            func.coalesce(
                func.sum(BankTransaction.amount),
                0
            )
        )
        .filter(
            BankTransaction.business_id == business_id,
            BankTransaction.txn_type == "CREDIT",
            BankTransaction.category == "customer_receipt"
        )
        .scalar()
    )

    total_bank_credits = Decimal(str(total_bank_credits or 0))

    # Avoid fake /12 division
    # Use GST filing periods as practical monthly denominator
    avg_monthly_bank = (
        total_bank_credits / Decimal(str(total_periods))
        if total_periods > 0 else Decimal("0")
    )

    # --------------------------------------------------
    # 4. Revenue Match Ratio
    # --------------------------------------------------

    revenue_match = 0.0

    if (
        avg_monthly_gst_turnover > 0
        and avg_monthly_bank > 0
    ):
        smaller = min(
            avg_monthly_gst_turnover,
            avg_monthly_bank
        )

        larger = max(
            avg_monthly_gst_turnover,
            avg_monthly_bank
        )

        revenue_match = float(smaller / larger)

    # --------------------------------------------------
    # 5. Compliance Score
    # --------------------------------------------------

    compliance_score = int(
        (filing_rate * 70)
        + (b2b_ratio * 20)
        + (min(revenue_match, 1.0) * 10)
    )

    compliance_score = max(
        0,
        min(100, compliance_score)
    )

    # Explainable lender-friendly band
    if compliance_score >= 80:
        risk_band = "healthy"
    elif compliance_score >= 60:
        risk_band = "caution"
    else:
        risk_band = "high_risk"

    # --------------------------------------------------
    # 6. Final Output
    # --------------------------------------------------

    gst_signals = {
        "total_periods": total_periods,
        "filing_rate": round(filing_rate, 3),
        "filed_on_time": filed_on_time,

        "avg_monthly_turnover": float(
            avg_monthly_gst_turnover
        ),

        "b2b_ratio": round(b2b_ratio, 3),

        "revenue_match_ratio": round(
            revenue_match,
            3
        ),

        "compliance_score": compliance_score,
        "risk_band": risk_band,
        "has_real_data": True
    }

    logger.info(
        f"[GSTAnalyzer] "
        f"Score={compliance_score} | "
        f"Band={risk_band} | "
        f"Revenue Match={revenue_match:.2f}"
    )

    return {
        **state,
        "gst_signals": gst_signals
    }