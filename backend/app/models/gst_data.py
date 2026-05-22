import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base

class GSTFiling(Base):
    __tablename__ = "gst_filings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    return_type = Column(String(20))
    tax_period = Column(String(7), nullable=False)     # 2024-03
    filing_date = Column(Date)
    due_date = Column(Date)
    filed_on_time = Column(Boolean)
    taxable_turnover = Column(Numeric(15, 2))
    total_tax_paid = Column(Numeric(15, 2))
    igst_amount = Column(Numeric(15, 2))
    cgst_amount = Column(Numeric(15, 2))
    sgst_amount = Column(Numeric(15, 2))
    b2b_turnover = Column(Numeric(15, 2))
    b2c_turnover = Column(Numeric(15, 2))
    status = Column(String(20))
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())