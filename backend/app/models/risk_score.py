import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, unique=True)
    score = Column(Integer, nullable=False)            # 300-900
    grade = Column(String(2))
    cash_flow_score = Column(Integer)
    gst_compliance_score = Column(Integer)
    payment_discipline_score = Column(Integer)
    business_vintage_score = Column(Integer)
    revenue_growth_score = Column(Integer)
    recommended_limit = Column(Numeric(15, 2))
    recommended_tenure_months = Column(Integer)
    flags = Column(ARRAY(String))
    positive_factors = Column(ARRAY(String))
    improvement_areas = Column(ARRAY(String))
    model_version = Column(String(20))
    confidence = Column(Numeric(4, 3))
    data_months = Column(Integer)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    raw_signals = Column(JSONB)