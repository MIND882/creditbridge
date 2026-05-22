from app.agents.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def risk_scorer_node(state: AgentState) -> AgentState:
    """
    Converts bank + GST signals into a 300–900 credit score
    """

    if state.get("error"):
        return state

    bank = state.get("bank_signals", {})
    gst = state.get("gst_signals", {})

    # --------------------------------------------------
    # 1. Cash Flow Score (0–100)
    # --------------------------------------------------

    monthly_revenue = bank.get("avg_monthly_revenue", 0)

    if monthly_revenue >= 5000000:        # ₹50L+
        cash_flow_score = 95
    elif monthly_revenue >= 3000000:      # ₹30L+
        cash_flow_score = 80
    elif monthly_revenue >= 1000000:      # ₹10L+
        cash_flow_score = 65
    elif monthly_revenue >= 500000:       # ₹5L+
        cash_flow_score = 50
    else:
        cash_flow_score = 30

    # --------------------------------------------------
    # 2. Payment Discipline Score (0–100)
    # --------------------------------------------------

    bounce_count = bank.get("bounce_count", 0)

    if bounce_count == 0:
        payment_score = 100
    elif bounce_count <= 2:
        payment_score = 75
    elif bounce_count <= 5:
        payment_score = 50
    else:
        payment_score = 25

    # --------------------------------------------------
    # 3. Revenue Consistency Score (0–100)
    # --------------------------------------------------

    consistency_score = bank.get(
        "consistency_score",
        50
    )

    # --------------------------------------------------
    # 4. GST Compliance Score (REAL GST signals)
    # --------------------------------------------------

    gst_score = gst.get(
        "compliance_score",
        75
    )

    # Revenue Match Bonus / Penalty
    revenue_match = gst.get(
        "revenue_match_ratio",
        0.90
    )

    if revenue_match < 0.70:
        # Major mismatch → lender red flag
        gst_score = max(
            0,
            gst_score - 20
        )

    elif revenue_match > 0.90:
        # Strong alignment → positive signal
        gst_score = min(
            100,
            gst_score + 5
        )

    # --------------------------------------------------
    # 5. Business Vintage Score (temporary default)
    # --------------------------------------------------

    vintage_score = 60

    # --------------------------------------------------
    # Weighted Final Score
    # --------------------------------------------------

    weighted_score = (
        (cash_flow_score * 0.35) +
        (payment_score * 0.25) +
        (consistency_score * 0.20) +
        (gst_score * 0.12) +
        (vintage_score * 0.08)
    )

    # Convert to 300–900 range
    final_score = int(
        300 + (weighted_score / 100) * 600
    )

    # --------------------------------------------------
    # Grade
    # --------------------------------------------------

    if final_score >= 800:
        grade = "A+"
    elif final_score >= 750:
        grade = "A"
    elif final_score >= 700:
        grade = "B+"
    elif final_score >= 650:
        grade = "B"
    elif final_score >= 600:
        grade = "C+"
    else:
        grade = "C"

    # --------------------------------------------------
    # Recommended Loan Limit
    # --------------------------------------------------

    if final_score >= 700:
        multiplier = 2.0
    elif final_score >= 600:
        multiplier = 1.5
    else:
        multiplier = 1.0

    recommended_limit = (
        monthly_revenue * multiplier
    )

    # --------------------------------------------------
    # Flags
    # --------------------------------------------------

    flags = []

    if bounce_count > 0:
        flags.append("has_bounces")

    if consistency_score < 60:
        flags.append("inconsistent_revenue")

    if bank.get(
        "top_customer_concentration",
        0
    ) > 60:
        flags.append(
            "customer_concentration_risk"
        )

    if revenue_match < 0.70:
        flags.append(
            "gst_bank_mismatch"
        )

    # --------------------------------------------------
    # Positive Factors
    # --------------------------------------------------

    positives = []

    if bounce_count == 0:
        positives.append(
            "Zero bounce record — excellent payment discipline"
        )

    if cash_flow_score >= 80:
        positives.append(
            "Strong monthly revenue above ₹30L"
        )

    if consistency_score >= 75:
        positives.append(
            "Consistent monthly cash flows"
        )

    if revenue_match > 0.90:
        positives.append(
            "Strong GST and bank revenue alignment"
        )

    # --------------------------------------------------
    # Improvement Areas
    # --------------------------------------------------

    improvements = []

    if not gst.get("has_real_data", False):
        improvements.append(
            "Add real GST filing data for stronger underwriting"
        )

    if revenue_match < 0.70:
        improvements.append(
            "Improve GST-bank revenue consistency"
        )

    if bounce_count > 0:
        improvements.append(
            "Reduce cheque/payment bounce incidents"
        )

    if not improvements:
        improvements.append(
            "Maintain current financial discipline"
        )

    # --------------------------------------------------
    # Final Output
    # --------------------------------------------------

    risk_score = {
    "score": final_score,
    "grade": grade,

    "cash_flow_score": cash_flow_score,
    "payment_discipline_score": payment_score,
    "gst_compliance_score": gst_score,

    # Temporary placeholder until real growth model added
    "revenue_growth_score": 70,

    # Temporary default until business age logic added
    "business_vintage_score": vintage_score,

    "recommended_limit": recommended_limit,
    "recommended_tenure_months": 12,

    "flags": flags,
    "positive_factors": positives,
    "improvement_areas": improvements,

    "confidence": 0.82,
    "data_months": bank.get(
        "months_of_data",
        12
    )
}

    logger.info(
        f"[RiskScorer] "
        f"Score={final_score} ({grade}) | "
        f"GST={gst_score} | "
        f"Limit=₹{recommended_limit:,.0f}"
    )

    return {
        **state,
        "risk_score": risk_score
    }