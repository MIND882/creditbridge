import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base

class Consent(Base):
    __tablename__ = "consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    aa_consent_id = Column(String(255), unique=True)
    aa_consent_handle = Column(String(255))
    consent_types = Column(ARRAY(String))
    data_date_from = Column(Date, nullable=False)
    data_date_to = Column(Date, nullable=False)
    status = Column(String(20), default="pending")
    expires_at = Column(DateTime(timezone=True))
    purpose = Column(String(100), default="credit_assessment")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True))