import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base

class Lender(Base):
    __tablename__ = "lenders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(20))
    contact_email = Column(String(255))
    contact_name = Column(String(255))
    api_key = Column(String(64), unique=True, nullable=False)
    

    min_score = Column(Integer)
    min_vintage_months = Column(Integer)
    min_monthly_turnover = Column(Numeric(15, 2))
    max_loan_amount = Column(Numeric(15, 2))
    min_loan_amount = Column(Numeric(15, 2))
    interest_rate_min = Column(Numeric(5, 2))
    interest_rate_max = Column(Numeric(5, 2))
    processing_fee_pct = Column(Numeric(4, 2))
    api_endpoint = Column(String(255))
    api_key_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LoanOffer(Base):
    __tablename__ = "loan_offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    lender_id = Column(UUID(as_uuid=True), ForeignKey("lenders.id"), nullable=False)
    risk_score_id = Column(UUID(as_uuid=True), ForeignKey("risk_scores.id"), nullable=False)
    offered_amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    processing_fee = Column(Numeric(10, 2))
    emi_amount = Column(Numeric(10, 2))
    status = Column(String(20), default="pending")
    offer_expires_at = Column(DateTime(timezone=True))
    our_fee_amount = Column(Numeric(10, 2))
    our_fee_pct = Column(Numeric(4, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    disbursed_at = Column(DateTime(timezone=True))