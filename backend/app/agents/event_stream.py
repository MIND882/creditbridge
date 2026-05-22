"""
event_stream.py — Redis Stream based event queue

Flow:
  Payment webhook / invoice paid
      ↓
  publish_transaction_event()   ← sirf event Redis mein daalo
      ↓
  Redis Stream: "txn_events"
      ↓
  EventStreamConsumer.start()   ← background worker reads + processes
      ↓
  process_transaction_event()   ← score refresh, alerts, invoice match
"""

import json
import asyncio
import redis.asyncio as aioredis
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.config import settings
from app.utils.logger import get_logger
from app.agents.event_processor import TransactionEvent, process_transaction_event

logger = get_logger(__name__)

# ─── Stream config ─────────────────────────────────────────────────────────────
STREAM_KEY     = "txn_events"
CONSUMER_GROUP = "intelligence_group"
CONSUMER_NAME  = "worker_1"
BLOCK_MS       = 2000   # wait 2s for new events before looping
MAX_RETRY      = 3      # retry failed events this many times


# ─── Redis connection ──────────────────────────────────────────────────────────
def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )


# ─── Publish ───────────────────────────────────────────────────────────────────
async def publish_transaction_event(
    business_id: str,
    txn_type: str,       # "CREDIT" | "DEBIT"
    amount: float,
    category: str,       # "customer_receipt" | "bounce" | "loan_emi" | ...
    counterparty: str = None,
) -> str:
    """
    Sirf event Redis stream mein daalo.
    Har jagah se call karo — webhook, invoice paid, CSV import.
    Returns: event_id
    """
    r = _get_redis()
    try:
        payload = {
            "business_id":  business_id,
            "txn_type":     txn_type,
            "amount":       str(amount),
            "category":     category,
            "counterparty": counterparty or "",
        }
        event_id = await r.xadd(STREAM_KEY, payload)
        logger.info(f"[EventStream] Published {txn_type} ₹{amount:,.0f} → {event_id}")
        return event_id
    finally:
        await r.aclose()


# ─── Sync wrapper (for FastAPI sync routes / webhooks) ─────────────────────────
def publish_event_sync(
    business_id: str,
    txn_type: str,
    amount: float,
    category: str,
    counterparty: str = None,
) -> str:
    """
    Sync version — use this inside FastAPI sync endpoints.
    Example: payments.py webhook mein call karo.
    """
    import redis as syncredis
    r = syncredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        payload = {
            "business_id":  business_id,
            "txn_type":     txn_type,
            "amount":       str(amount),
            "category":     category,
            "counterparty": counterparty or "",
        }
        event_id = r.xadd(STREAM_KEY, payload)
        logger.info(f"[EventStream] Sync published {txn_type} ₹{amount:,.0f} → {event_id}")
        return event_id
    finally:
        r.close()


# ─── Consumer ──────────────────────────────────────────────────────────────────
class EventStreamConsumer:
    """
    Background worker — Redis stream se events padhta hai
    aur process_transaction_event() call karta hai.

    FastAPI startup mein start karo:
        @app.on_event("startup")
        async def startup():
            asyncio.create_task(EventStreamConsumer().start())
    """

    def __init__(self):
        self._running = False

    async def _ensure_group(self, r: aioredis.Redis):
        """Consumer group create karo agar exist nahi karta."""
        try:
            await r.xgroup_create(
                STREAM_KEY,
                CONSUMER_GROUP,
                id="0",          # process from beginning
                mkstream=True    # stream bhi create karo agar nahi hai
            )
            logger.info(f"[EventStream] Consumer group '{CONSUMER_GROUP}' created")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                pass  # already exists — theek hai
            else:
                logger.error(f"[EventStream] Group create failed: {e}")

    async def start(self):
        """Main loop — forever events padhta rahega."""
        self._running = True
        logger.info("[EventStream] Consumer started — waiting for events...")

        r = _get_redis()
        await self._ensure_group(r)

        while self._running:
            try:
                # Read new events from stream
                messages = await r.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={STREAM_KEY: ">"},  # ">" = only new, unprocessed
                    count=10,
                    block=BLOCK_MS
                )

                if not messages:
                    continue

                for stream_name, events in messages:
                    for event_id, data in events:
                        await self._handle_event(r, event_id, data)

            except asyncio.CancelledError:
                logger.info("[EventStream] Consumer cancelled — shutting down")
                break
            except Exception as e:
                logger.error(f"[EventStream] Consumer error: {e}")
                await asyncio.sleep(2)  # brief pause before retry

        await r.aclose()
        logger.info("[EventStream] Consumer stopped")

    async def _handle_event(self, r: aioredis.Redis, event_id: str, data: dict):
        """Ek event process karo."""
        db: Session = SessionLocal()
        try:
            event = TransactionEvent(
                business_id  = data["business_id"],
                txn_type     = data["txn_type"],
                amount       = float(data["amount"]),
                category     = data["category"],
                counterparty = data.get("counterparty") or None,
            )

            result = process_transaction_event(event, db)

            # Acknowledge — Redis ko batao yeh event done hai
            await r.xack(STREAM_KEY, CONSUMER_GROUP, event_id)

            # Log result
            alerts = result.get("alerts", [])
            score_old = result.get("old_score")
            score_new = result.get("new_score")
            logger.info(
                f"[EventStream] ✓ {event_id} | "
                f"Score: {score_old}→{score_new} | "
                f"Alerts: {len(alerts)}"
            )

            # Push critical alerts to lender feed
            if alerts:
                critical = [a for a in alerts if a.get("severity") == "critical"]
                if critical:
                    await _push_lender_alert(r, data["business_id"], critical)

        except Exception as e:
            logger.error(f"[EventStream] Event {event_id} failed: {e}")
            # Don't ack — will be retried via pending list
        finally:
            db.close()

    def stop(self):
        self._running = False


# ─── Lender alert feed ─────────────────────────────────────────────────────────
async def _push_lender_alert(r: aioredis.Redis, business_id: str, alerts: list):
    """
    Critical alerts lender feed mein push karo.
    Lender dashboard yahan se real-time updates leta hai.
    """
    for alert in alerts:
        payload = json.dumps({
            "business_id": business_id,
            "type":        alert["type"],
            "severity":    alert["severity"],
            "message":     alert["message"],
            "action":      alert.get("action", ""),
        })
        # Lender-specific channel mein publish karo
        await r.lpush(f"lender_alerts:{business_id}", payload)
        await r.ltrim(f"lender_alerts:{business_id}", 0, 99)  # max 100 alerts

        # Global alert feed bhi
        await r.lpush("lender_alerts:all", payload)
        await r.ltrim("lender_alerts:all", 0, 499)  # max 500 global

    logger.info(f"[EventStream] {len(alerts)} critical alert(s) pushed to lender feed")


# ─── Lender alert fetch (for API) ──────────────────────────────────────────────
def get_lender_alerts_sync(business_id: str = None, limit: int = 20) -> list:
    """
    Lender dashboard ke liye alerts fetch karo.
    business_id=None → sab businesses ke alerts
    """
    import redis as syncredis
    r = syncredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        key = f"lender_alerts:{business_id}" if business_id else "lender_alerts:all"
        raw = r.lrange(key, 0, limit - 1)
        return [json.loads(item) for item in raw]
    finally:
        r.close()


# ─── Pending events retry (run on startup) ─────────────────────────────────────
async def retry_pending_events():
    """
    Server restart ke baad pending (unacknowledged) events retry karo.
    Startup mein call karo.
    """
    r = _get_redis()
    try:
        pending = await r.xpending_range(
            STREAM_KEY, CONSUMER_GROUP,
            min="-", max="+", count=100
        )
        if not pending:
            return

        logger.info(f"[EventStream] {len(pending)} pending events found — retrying")

        consumer = EventStreamConsumer()
        for item in pending:
            event_id = item["message_id"]
            # Claim the message
            claimed = await r.xautoclaim(
                STREAM_KEY, CONSUMER_GROUP, CONSUMER_NAME,
                min_idle_time=60000,  # 1 minute idle
                start_id=event_id, count=1
            )
            if claimed and claimed[1]:
                for eid, data in claimed[1]:
                    await consumer._handle_event(r, eid, data)
    except Exception as e:
        logger.error(f"[EventStream] Retry failed: {e}")
    finally:
        await r.aclose()