import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lender_id = Column(UUID(as_uuid=True), ForeignKey("lenders.id"), nullable=True)
    business_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(50))        # viewed_pool, viewed_business, approved, rejected
    endpoint = Column(String(255))
    request_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())