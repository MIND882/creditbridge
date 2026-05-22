import uuid 
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base

class Rejection(Base):
    __tablename__ = "rejections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    lender_id = Column(UUID(as_uuid=True), ForeignKey("lenders.id"), nullable=True)

    # what was the score at time of rejection
    score_at_rejection = Column(Integer)
    grade_at_rejection = Column(String(2))
    
      # Why rejected — primary reason
    rejection_reason = Column(String(50))      # score_too_low, gst_mismatch,
                                               # low_vintage, low_turnover,
                                               # high_bounce, sector_risk,
                                               # incomplete_data
    rejection_detail = Column(Text)            # Human readable explanation
    rejected_by = Column(String(20))           # lender, system, manual_review

    # What needs to improve
    improvement_needed = Column(JSONB)         # {"score_gap": 50, "gst_needed": True}

    # Manual review fields
    reviewed_by = Column(String(100))          # Reviewer name (you, initially)
    review_notes = Column(Text)
    reviewed_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
