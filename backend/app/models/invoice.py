import uuid
from sqlalchemy import Column, String, DateTime, Numeric, Date, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)

    # Invoice details
    invoice_number = Column("Invoice_number", String(50), nullable=False)
    invoice_date = Column("Invoice_date", Date, nullable=False)
    due_date = Column("Due_date", Date, nullable=False)

    # party detail buyer or supplier name
    party_name = Column(String(255), nullable=False)  # buyer or supplier name
    party_gstin = Column(String(15), nullable=True)  # buyer or supplier GSTIN
    party_phone = Column(String(15), nullable=True)

    # type of invoice
    invoice_type = Column(String(20), nullable=False)  # e.g., receivable or payable

    # amounts
    subtotal = Column(Numeric(15, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=18.0)
    gst_amount = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2), nullable=False)
    # Status
    status = Column(String(20), default="pending")     # pending, partial, paid, overdue
    paid_amount = Column(Numeric(15, 2), default=0)
    paid_date = Column(Date)

    # Days overdue (computed)
    days_overdue = Column(Integer, default=0)

    # Notes
    description = Column(Text)
    raw_data = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Backward-compatible accessors for legacy code paths.
    @property
    def Invoice_number(self):
        return self.invoice_number

    @Invoice_number.setter
    def Invoice_number(self, value):
        self.invoice_number = value

    @property
    def Invoice_date(self):
        return self.invoice_date

    @Invoice_date.setter
    def Invoice_date(self, value):
        self.invoice_date = value

    @property
    def Due_date(self):
        return self.due_date

    @Due_date.setter
    def Due_date(self, value):
        self.due_date = value


class PaymentReminder(Base):
    __tablename__ = "payment_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)

    reminder_type = Column(String(20))   # whatsapp, sms, email
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="sent")  # sent, delivered, failed
    message = Column(Text)
