import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    consent_id = Column(UUID(as_uuid=True), ForeignKey("consents.id"), nullable=True)
    bank_name = Column(String(100))
    account_type = Column(String(20))
    masked_account = Column(String(20))
    ifsc = Column(String(11))
    avg_monthly_balance = Column(Numeric(15, 2))
    avg_monthly_credits = Column(Numeric(15, 2))
    avg_monthly_debits = Column(Numeric(15, 2))
    bounce_count_12m = Column(Integer, default=0)
    last_fetched_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    txn_date = Column(DateTime(timezone=True), nullable=False)
    value_date = Column(DateTime(timezone=True))
    amount = Column(Numeric(15, 2), nullable=False)
    txn_type = Column(String(10), nullable=False)      # CREDIT / DEBIT
    balance = Column(Numeric(15, 2))
    narration = Column(Text)
    category = Column(String(50))
    counterparty = Column(String(255))
    is_recurring = Column(Boolean, default=False)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())