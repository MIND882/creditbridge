import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, business, consent, data, intelligence, lender, loans, invoices, upload, payments, documents, kyc
from app.db.session import engine
from app.models import Base
from app.agents.event_stream import EventStreamConsumer, retry_pending_events
from app.utils.logger import get_logger

logger = get_logger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MSME Credit Intelligence Platform",
    version="1.0.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/v1/auth",          tags=["auth"])
app.include_router(consent.router,       prefix="/v1/consent",       tags=["consent"])
app.include_router(data.router,          prefix="/v1/data",           tags=["data"])
app.include_router(intelligence.router,  prefix="/v1/intelligence",   tags=["intelligence"])
app.include_router(lender.router,        prefix="/v1/lenders",        tags=["lenders"])
app.include_router(loans.router,         prefix="/v1/loans",          tags=["loans"])
app.include_router(business.router,      prefix="/v1/businesses",      tags=["businesses"])
app.include_router(invoices.router,      prefix="/v1/invoices",       tags=["invoices"])
app.include_router(upload.router,        prefix="/v1/upload",         tags=["upload"])
app.include_router(kyc.router,           prefix="/v1/kyc",            tags=["kyc"])
app.include_router(payments.router,      prefix="/v1/payments",       tags=["payments"])
app.include_router(documents.router,     prefix="/v1/documents",      tags=["documents"])


# ─── Event Stream Lifecycle ────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """
    Server start hone par:
    1. Pending (unacknowledged) events retry karo
    2. Event stream consumer background mein start karo
    """
    logger.info("[Startup] MSME Platform starting...")

    # Redis chal raha hai? — check karo gracefully
    try:
        await retry_pending_events()
        logger.info("[Startup] Pending events retry done")
    except Exception as e:
        logger.warning(f"[Startup] Redis not available — event stream disabled: {e}")
        return  # Redis nahi hai toh consumer start mat karo

    # Background consumer start karo
    asyncio.create_task(EventStreamConsumer().start())
    logger.info("[Startup] Event stream consumer started ✓")


@app.on_event("shutdown")
async def shutdown():
    logger.info("[Shutdown] MSME Platform shutting down...")


# ─── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "msme-platform"}
