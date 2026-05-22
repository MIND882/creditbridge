from sqlalchemy.orm import Session
from app.agents.state import AgentState
from app.agents.bank_analyzer import bank_analyzer_node
from app.agents.gst_analyzer import gst_analyzer_node
from app.agents.risk_scorer import risk_scorer_node
from app.models.risk_score import RiskScore
from app.utils.logger import get_logger

from datetime import datetime, timedelta
from uuid import UUID

logger = get_logger(__name__)


def run_intelligence_pipeline(
    business_id: str,
    db: Session
) -> dict:
    """
    Full Intelligence Pipeline

    Flow:
    Bank Analyzer
    → GST Analyzer
    → Risk Scorer
    → Save Risk Score to DB
    """

    logger.info(
        f"[Pipeline] Starting intelligence pipeline for {business_id}"
    )

    # Validate UUID once only
    try:
        business_uuid = UUID(business_id)
    except Exception:
        logger.exception("[Pipeline] Invalid business_id")

        return {
            "error": "Invalid business_id"
        }

    # -----------------------------------------
    # Initial State
    # -----------------------------------------

    state: AgentState = {
        "business_id": business_uuid,
        "bank_signals": None,
        "gst_signals": None,
        "risk_score": None,
        "loan_offers": None,
        "error": None
    }

    # -----------------------------------------
    # Step 1: Bank Analysis
    # -----------------------------------------

    state = bank_analyzer_node(state, db)

    if state.get("error"):
        logger.error(
            f"[Pipeline] Bank analyzer failed: {state['error']}"
        )

        return {
            "error": state["error"]
        }

    # -----------------------------------------
    # Step 2: GST Analysis
    # -----------------------------------------

    state = gst_analyzer_node(state, db)

    if state.get("error"):
        logger.error(
            f"[Pipeline] GST analyzer failed: {state['error']}"
        )

        return {
            "error": state["error"]
        }

    # -----------------------------------------
    # Step 3: Risk Scoring
    # -----------------------------------------

    state = risk_scorer_node(state)

    if state.get("error"):
        logger.error(
            f"[Pipeline] Risk scorer failed: {state['error']}"
        )

        return {
            "error": state["error"]
        }

    risk = state["risk_score"]

    # -----------------------------------------
    # Step 4: Save / Update DB
    # -----------------------------------------

    now = datetime.utcnow()
    expiry = now + timedelta(days=30)

    raw_signals = {
        "bank_signals": state.get("bank_signals"),
        "gst_signals": state.get("gst_signals")
    }

    try:
        existing = (
            db.query(RiskScore)
            .filter(
                RiskScore.business_id == business_uuid
            )
            .first()
        )

        fields_to_save = {
            "score": risk["score"],
            "grade": risk["grade"],

            "cash_flow_score": risk["cash_flow_score"],
            "payment_discipline_score": risk["payment_discipline_score"],
            "gst_compliance_score": risk["gst_compliance_score"],
            "revenue_growth_score": risk["revenue_growth_score"],
            "business_vintage_score": risk["business_vintage_score"],

            "recommended_limit": risk["recommended_limit"],
            "recommended_tenure_months": risk["recommended_tenure_months"],

            "flags": risk["flags"],
            "positive_factors": risk["positive_factors"],
            "improvement_areas": risk["improvement_areas"],

            "confidence": risk["confidence"],
            "data_months": risk["data_months"],

            "computed_at": now,
            "expires_at": expiry,
            "model_version": "v1.1",

            "raw_signals": raw_signals
        }

        if existing:
            # Update existing record
            for key, value in fields_to_save.items():
                setattr(existing, key, value)

            logger.info(
                f"[Pipeline] Updated existing RiskScore for {business_id}"
            )

        else:
            # Create new record
            risk_record = RiskScore(
                business_id=business_uuid,
                **fields_to_save
            )

            db.add(risk_record)

            logger.info(
                f"[Pipeline] Created new RiskScore for {business_id}"
            )

        db.commit()

    except Exception:
        db.rollback()

        logger.exception(
            "[Pipeline] Failed while saving RiskScore"
        )

        return {
            "error": "Failed to save risk score"
        }

    logger.info(
        f"[Pipeline] Complete | "
        f"Score: {risk['score']} | "
        f"Grade: {risk['grade']}"
    )

    return risk