from twilio.rest import Client
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def get_twilio_client():
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials are not set. SMS notifications will not work.")
        return None
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_whatsapp(to_phone: str, message: str) -> bool:
    """Send WhatsApp message via Twilio."""
    client = get_twilio_client()
    if not client:
        logger.info(f"[MOCK WhatsApp] To: {to_phone} | {message}")
        return True

    try:
        whatsapp_from = settings.TWILIO_WHATSAPP_FROM
        if not whatsapp_from:
            logger.warning("TWILIO_WHATSAPP_FROM missing. Using mock WhatsApp delivery.")
            logger.info(f"[MOCK WhatsApp] To: {to_phone} | {message}")
            return True

        msg = client.messages.create(
            from_=whatsapp_from,
            to=f"whatsapp:+91{to_phone}",
            body=message
        )
        logger.info(f"WhatsApp sent: {msg.sid} to {to_phone}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp failed: {e}")
        return False
# ─── Message Templates ────────────────────────────────────────────

def notify_score_ready(phone: str, business_name: str, score: int, grade: str, limit: float):
    message = f"""✅ *CreditBridge Score Ready*

Business: {business_name}
Score: *{score}/900* ({grade} Grade)
Loan Limit: *₹{limit/100000:.0f}L*

Aapka credit score taiyaar hai. Login karein loan offers dekhne ke liye.
🔗 http://localhost:5173/dashboard

_Powered by CreditBridge_"""
    return send_whatsapp(phone, message)


def notify_loan_accepted(phone: str, business_name: str, lender: str, amount: float, rate: float):
    message = f"""🎉 *Loan Offer Accepted!*

Business: {business_name}
Lender: *{lender}*
Amount: *₹{amount/100000:.0f}L*
Rate: {rate}% per annum

Lender 24 ghante mein contact karega.
Documents ready rakhein: PAN, GST, Bank statements.

_CreditBridge_"""
    return send_whatsapp(phone, message)


def notify_invoice_overdue(phone: str, business_name: str, party_name: str, amount: float, days: int):
    message = f"""⚠️ *Payment Overdue Alert*

{business_name}
Party: *{party_name}*
Amount: *₹{amount/100000:.1f}L*
Overdue: {days} days

Invoice follow-up karna recommended hai.

_CreditBridge Invoice Tracker_"""
    return send_whatsapp(phone, message)


def notify_ca_commission(phone: str, ca_name: str, business_name: str, loan_amount: float, commission: float):
    message = f"""💰 *Commission Earned!*

{ca_name} ji,
{business_name} ka loan disbursed hua.
Loan Amount: ₹{loan_amount/100000:.0f}L
*Aapka Commission: ₹{commission:,.0f}*

Amount 3-5 business days mein transfer hoga.

_CreditBridge Partner Program_"""
    return send_whatsapp(phone, message)
