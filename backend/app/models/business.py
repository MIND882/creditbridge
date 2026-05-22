import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  # Use PostgreSQL-specific UUID type , AND MEANING OF uuid IS " UNIVERSALLY UNQIUE INENTIFIRER"
from sqlalchemy.sql import func
from app.db.session import Base


class CAPartner(Base):
    __tablename__ = "ca_partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    firm_name = Column(String(255))
    phone = Column(String(15), nullable=False)
    email = Column(String(255))
    city = Column(String(100))
    total_referrals = Column(Integer, default=0)
    successful_loans = Column(Integer, default=0)
    total_commission_earned = Column(Numeric(15, 2), default=0)
    commission_pct = Column(Numeric(4, 2), default=0.5)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pan = Column(String(10), unique=True, nullable=False)
    gstin = Column(String(15), unique=True)
    business_name = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    owner_phone = Column(String(15), nullable=False)
    owner_email = Column(String(255))
    business_type = Column(String(50))
    city = Column(String(100))
    state = Column(String(100))
    vintage_years = Column(Numeric(4, 1))
    status = Column(String(20), default="pending")
    onboarding_step = Column(Integer, default=0)
    ca_partner_id = Column(UUID(as_uuid=True), ForeignKey("ca_partners.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())