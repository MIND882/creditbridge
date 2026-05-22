import razorpay
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.warning("Razorpay credentials are missing. Falling back to mock payment links.")
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_payment_link(
    business_id: str,
    amount: int,  # rupees
    invoice_number: str,
    party_name: str,
    description: str,
) -> dict:
    client = get_razorpay_client()

    if not client:
        return {
            "payment_link_id": f"mock_plink_{invoice_number}",
            "short_url": f"https://rzp.io/i/mock-{invoice_number}",
            "amount": amount,
            "status": "mock",
        }

    if amount <= 0 or amount > 5000000:  # 50 lakh INR max
        raise ValueError(f"Amount {amount} too large. Max allowed: 50L INR")
    if len(party_name) > 100:
        raise ValueError("Party name too long")

    # Razorpay test mode cap (paise)
    amount_paise = min(int(amount * 100), 49999900)
    logger.info(f"Input: amount={amount} INR -> {amount_paise} paise")

    try:
        payment_link = client.payment_link.create({
            "amount": amount_paise,
            "currency": "INR",
            "description": f"Invoice {invoice_number} - {description}",
            "customer": {"name": party_name.strip()},
            "notify": {"sms": True, "email": False},
            "reminder_enable": True,
            "notes": {
                "business_id": business_id,
                "invoice_number": invoice_number,
            },
        })

        logger.info(f"Payment link created: {payment_link['id']}")
        return {
            "payment_link_id": payment_link["id"],
            "short_url": payment_link["short_url"],
            "amount": amount,
            "status": payment_link["status"],
        }

    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay validation failed: {e}")
        raise ValueError(f"Payment creation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def verify_payment_webhook(payload: dict, signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    client = get_razorpay_client()
    if not client:
        return True  # mock mode

    if not settings.RAZORPAY_WEBHOOK_SECRET:
        logger.warning("RAZORPAY_WEBHOOK_SECRET missing. Webhook signature verification skipped.")
        return True

    try:
        client.utility.verify_webhook_signature(
            str(payload),
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
        )
        return True
    except Exception:
        return False
