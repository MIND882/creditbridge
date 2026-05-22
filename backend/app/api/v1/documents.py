from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.business import Business
from app.models.risk_score import RiskScore
from app.services.loan_file_pdf import generate_loan_package_pdf
from app.services.financial_statements import (
    generate_pl_statement,
    generate_cash_flow,
    generate_working_capital_analysis
)
from uuid import UUID

router = APIRouter()


@router.get("/pl/{business_id}")
def get_pl_statement(business_id: str, db: Session = Depends(get_db)):
    """Auto-generated P&L statement from bank transactions."""
    business = db.query(Business).filter(
        Business.id == UUID(business_id)
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    pl = generate_pl_statement(business_id, db)

    return {
        "business": business.business_name,
        "gstin": business.gstin,
        "statement_type": "Profit & Loss",
        "generated_at": "Auto-generated from bank transactions",
        **pl
    }


@router.get("/cashflow/{business_id}")
def get_cash_flow(business_id: str, db: Session = Depends(get_db)):
    """Auto-generated Cash Flow Statement."""
    business = db.query(Business).filter(
        Business.id == UUID(business_id)
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    cf = generate_cash_flow(business_id, db)

    return {
        "business": business.business_name,
        "statement_type": "Cash Flow Statement",
        "generated_at": "Auto-generated from bank transactions",
        **cf
    }


@router.get("/working-capital/{business_id}")
def get_working_capital(business_id: str, db: Session = Depends(get_db)):
    """Working capital analysis — loan need assessment."""
    wc = generate_working_capital_analysis(business_id, db)
    return wc


@router.get("/loan-package/{business_id}")
def get_complete_loan_package(business_id: str, db: Session = Depends(get_db)):
    """
    Complete loan file — everything bank needs in one call.
    This is the core product for lenders.
    """
    bid = UUID(business_id)

    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    score = db.query(RiskScore).filter(RiskScore.business_id == bid).first()
    if not score:
        raise HTTPException(status_code=404, detail="Run credit score first")

    pl = generate_pl_statement(business_id, db)
    cf = generate_cash_flow(business_id, db)
    wc = generate_working_capital_analysis(business_id, db)

    return {
        "loan_package": {
            "generated_at": str(__import__('datetime').datetime.utcnow()),
            "status": "COMPLETE",

            "business_profile": {
                "name": business.business_name,
                "owner": business.owner_name,
                "gstin": business.gstin,
                "pan": business.pan,
                "city": business.city,
                "business_type": business.business_type,
                "phone": business.owner_phone
            },

            "credit_assessment": {
                "score": score.score,
                "grade": score.grade,
                "recommended_limit": float(score.recommended_limit or 0),
                "confidence": float(score.confidence or 0),
                "flags": score.flags or [],
                "positive_factors": score.positive_factors or []
            },

            "financial_summary": {
                "avg_monthly_revenue": pl["summary"]["avg_monthly_revenue"],
                "gross_margin_pct": pl["summary"]["gross_margin_pct"],
                "net_margin_pct": pl["summary"]["net_margin_pct"],
                "profitable_months": pl["summary"]["profitable_months"],
                "data_months": pl["months"]
            },

            "cash_flow_summary": {
                "positive_months": cf["summary"]["positive_months"],
                "avg_monthly_inflow": cf["summary"]["avg_monthly_inflow"],
                "avg_net_cash_flow": cf["summary"]["avg_net_cash_flow"]
            },

            "working_capital": wc,

            "pl_statement": pl,
            "cash_flow_statement": cf,

            "lender_recommendation": {
                "decision": "APPROVE" if score.score >= 700 else "REVIEW",
                "suggested_amount": float(score.recommended_limit or 0),
                "tenure_months": score.recommended_tenure_months or 12,
                "basis": "Cash flow based lending — 12 months behavioral data"
            }
        }
    }
@router.get("/loan-package/{business_id}/pdf")
def download_loan_package_pdf(business_id: str, db: Session = Depends(get_db)):
    """Download complete loan package as PDF."""
    bid = UUID(business_id)

    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    score = db.query(RiskScore).filter(RiskScore.business_id == bid).first()
    if not score:
        raise HTTPException(status_code=404, detail="Run credit score first")

    # Get loan package data
    from app.services.financial_statements import (
        generate_pl_statement, generate_cash_flow, generate_working_capital_analysis
    )

    pl = generate_pl_statement(business_id, db)
    cf = generate_cash_flow(business_id, db)
    wc = generate_working_capital_analysis(business_id, db)

    loan_package = {
        "loan_package": {
            "generated_at": str(__import__('datetime').datetime.utcnow()),
            "status": "COMPLETE",
            "business_profile": {
                "name": business.business_name,
                "owner": business.owner_name,
                "gstin": business.gstin,
                "pan": business.pan,
                "city": business.city,
                "business_type": business.business_type,
                "phone": business.owner_phone
            },
            "credit_assessment": {
                "score": score.score,
                "grade": score.grade,
                "recommended_limit": float(score.recommended_limit or 0),
                "confidence": float(score.confidence or 0),
                "flags": score.flags or [],
                "positive_factors": score.positive_factors or []
            },
            "financial_summary": {
                "avg_monthly_revenue": pl["summary"]["avg_monthly_revenue"],
                "gross_margin_pct": pl["summary"]["gross_margin_pct"],
                "net_margin_pct": pl["summary"]["net_margin_pct"],
                "profitable_months": pl["summary"]["profitable_months"],
                "data_months": pl["months"]
            },
            "cash_flow_summary": {
                "positive_months": cf["summary"]["positive_months"],
                "avg_monthly_inflow": cf["summary"]["avg_monthly_inflow"],
                "avg_net_cash_flow": cf["summary"]["avg_net_cash_flow"]
            },
            "working_capital": wc,
            "pl_statement": pl,
            "cash_flow_statement": cf,
            "lender_recommendation": {
                "decision": "APPROVE" if score.score >= 700 else "REVIEW",
                "suggested_amount": float(score.recommended_limit or 0),
                "tenure_months": score.recommended_tenure_months or 12,
                "basis": "Cash flow based lending — 12 months behavioral data"
            }
        }
    }

    pdf_bytes = generate_loan_package_pdf(loan_package)

    filename = f"CreditBridge_{business.business_name.replace(' ', '_')}_LoanPackage.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )