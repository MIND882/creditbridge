from typing import TypedDict, Optional
from uuid import UUID

class AgentState(TypedDict):
    business_id: str
    bank_signals: Optional[dict]
    gst_signals: Optional[dict]
    risk_score: Optional[dict]
    loan_offers: Optional[list]
    error: Optional[str]