# CreditBridge — MSME Credit Intelligence Platform

> **The infrastructure layer for MSME lending in India.**
> Real-time credit scoring, AI-powered underwriting, and a live lender intelligence feed — built for the 64 million businesses that banks can't serve.

```
MSME Payment → Our Rails → Live Data → AI Intelligence → Lender Insight → Loan → Repayment → Better Score → Better Loan
                                    ↑_______________________________________________|
                                                   Closed Loop
```

---

## What Is This

CreditBridge is not a lending app. It is **financial infrastructure** — the layer that sits between MSMEs and lenders, converting raw transaction data into a real-time credit intelligence feed.

**The problem it solves:**
- 64 million MSMEs in India need credit
- Banks take 2-3 weeks to underwrite, demand collateral, reject 70% of applications
- MSMEs have rich financial data (bank transactions, GST returns, invoices) but no way to present it credibly

**What CreditBridge does:**
- Captures every MSME transaction in real time
- Runs AI agents on each transaction → updates credit score instantly
- Gives lenders a live, pre-underwritten MSME pool
- Reduces lender underwriting cost to near zero
- Reduces MSME loan approval time from weeks to hours

**The moat:** Every transaction strengthens the data advantage. A lender that switches loses the entire credit history of their portfolio.

---

## Architecture — 4 Levels

```
┌──────────────────────────────────────────────────────┐
│  LEVEL 1: PAYMENT RAIL                               │
│  Perfios AA → Bank feed | Razorpay → Payment capture │
│  CSV Upload → Instant data | GSP → GST returns       │
└─────────────────────────┬────────────────────────────┘
                          │ Redis event stream
┌─────────────────────────▼────────────────────────────┐
│  LEVEL 2: AI INTELLIGENCE                             │
│  6 agents fire on every transaction:                 │
│  TransactionClassifier → CashFlowForecaster          │
│  BuyerReliabilityScorer → RiskSignalDetector         │
│  CreditScoreEngine → LoanEligibilityEngine           │
└─────────────────────────┬────────────────────────────┘
                          │ risk signals
┌─────────────────────────▼────────────────────────────┐
│  LEVEL 3: CREDIT LAYER                               │
│  Risk scoring (0-900) | KYC via Surepass             │
│  Loan matching | Auto P&L | Loan file PDF            │
└─────────────────────────┬────────────────────────────┘
                          │ pre-underwritten deals
┌─────────────────────────▼────────────────────────────┐
│  LEVEL 4: LENDER INTELLIGENCE FEED                   │
│  Live MSME pool | Portfolio health | Early warnings  │
│  Real-time alerts | Risk analytics by sector         │
│  → Banks pay ₹1Cr/year for this feed                 │
└──────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11 · FastAPI · SQLAlchemy |
| Database | PostgreSQL · Redis (streams + cache) |
| AI/ML | LangGraph · Custom scoring agents |
| Frontend MSME | React 18 · TypeScript · Vite |
| Frontend Lender | React 18 · TypeScript · Vite |
| KYC | Surepass API (PAN + GSTIN + Digilocker) |
| Payments | Razorpay (payment links + webhook) |
| Bank Data | Perfios Account Aggregator |
| GST Data | GSP API (Masters India) |
| Notifications | Twilio WhatsApp |
| PDF Generation | ReportLab |
| Auth | JWT (MSME) · API Key (Lender) |

---

## Project Structure

```
msme-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py          # MSME register/login
│   │   │   ├── kyc.py           # PAN + GSTIN verification
│   │   │   ├── invoices.py      # Invoice CRUD
│   │   │   ├── payments.py      # Razorpay links + webhook
│   │   │   ├── intelligence.py  # Score compute API
│   │   │   ├── lender.py        # Lender portal API
│   │   │   ├── documents.py     # P&L + loan file PDF
│   │   │   ├── upload.py        # Bank CSV import
│   │   │   ├── consent.py       # AA consent flow
│   │   │   └── data.py          # Bank data fetch
│   │   │
│   │   ├── agents/
│   │   │   ├── pipeline.py              # Main orchestrator
│   │   │   ├── bank_analyzer.py         # Transaction analysis
│   │   │   ├── gst_analyzer.py          # GST compliance scoring
│   │   │   ├── risk_scorer.py           # Final score calculation
│   │   │   ├── buyer_scorer.py          # Per-buyer reliability
│   │   │   ├── cash_flow_forecaster.py  # 30/60/90 day forecast
│   │   │   ├── event_processor.py       # Real-time txn handler
│   │   │   └── event_stream.py          # Redis stream consumer
│   │   │
│   │   ├── services/
│   │   │   ├── kyc_service.py           # Surepass integration
│   │   │   ├── perfios_service.py       # Account Aggregator
│   │   │   ├── payment_service.py       # Razorpay
│   │   │   ├── financial_statements.py  # Auto P&L generation
│   │   │   ├── loan_file_pdf.py         # Lender PDF package
│   │   │   ├── lender_service.py        # Lender pool + portfolio
│   │   │   ├── loan_matcher.py          # MSME → lender matching
│   │   │   ├── gsp_service.py           # GST return data
│   │   │   ├── data_processor.py        # Signal computation
│   │   │   └── notification.py          # WhatsApp alerts
│   │   │
│   │   ├── models/                      # SQLAlchemy ORM models
│   │   │   ├── business.py
│   │   │   ├── bank_data.py
│   │   │   ├── invoice.py
│   │   │   ├── risk_score.py
│   │   │   ├── loan_offer.py
│   │   │   ├── gst_data.py
│   │   │   ├── consent.py
│   │   │   └── audit.py
│   │   │
│   │   ├── config.py                    # Settings + env vars
│   │   └── main.py                      # FastAPI app entry
│   │
│   └── tests/
│
├── frontend/                            # MSME App (React)
│   └── src/pages/
│       ├── Landing.tsx
│       ├── Register.tsx                 # With real KYC step
│       ├── Dashboard.tsx                # Score + sidebar nav
│       ├── InvoiceManager.tsx
│       ├── CreditScore.tsx
│       ├── FinancialStatements.tsx      # P&L + Cash Flow
│       ├── LoanOffers.tsx
│       ├── LoanApplication.tsx
│       ├── DocumentVault.tsx
│       └── ProfileSetup.tsx             # KYC verification UI
│
└── frontend-lender/                     # Lender Portal (React)
    └── src/pages/
        ├── Login.tsx
        ├── Pool.tsx                     # MSME pool table
        ├── BusinessDetail.tsx           # Deep dive + approve
        ├── Portfolio.tsx                # Active loan health
        ├── Alerts.tsx                   # Real-time warnings
        └── RiskIntelligence.tsx         # Sector analytics
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/creditbridge.git
cd creditbridge
```

### 2. Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment variables

Create `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/creditbridge
REDIS_URL=redis://localhost:6379

# App
SECRET_KEY=your-secret-key-here
APP_BASE_URL=http://localhost:8000
APP_ENV=development

# JWT
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_DAYS=7

# KYC — Surepass (get from surepass.io)
SUREPASS_API_TOKEN=eyJhbGci...
SUREPASS_BASE_URL=https://sandbox.surepass.io

# Payments — Razorpay (get from razorpay.com)
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Bank Data — Perfios AA (get from perfios.com/aa-developer)
PERFIOS_API_KEY=
PERFIOS_API_SECRET=
PERFIOS_BASE_URL=https://sandbox.perfios.com

# GST Data — Masters India GSP (get from mastergst.com)
GSP_API_KEY=
GSP_SECRET=
GSP_BASE_URL=https://api.mastergst.com

# Notifications — Twilio (get from twilio.com)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### 4. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 5. Start backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 6. Frontend (MSME App)

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 7. Frontend (Lender Portal)

```bash
cd frontend-lender
npm install
npm run dev
# → http://localhost:5174
```

---

## Key API Endpoints

### Auth

```
POST /v1/auth/register     Register MSME
POST /v1/auth/login        Login → JWT token
```

### KYC (Surepass)

```
POST /v1/kyc/pan           Verify PAN → name, DOB, Aadhaar link
POST /v1/kyc/gstin         Verify GSTIN → business name, status
POST /v1/kyc/msme          Combined PAN + GSTIN → KYC score
GET  /v1/kyc/health        Check Surepass connection
```

### Bank Data

```
POST /v1/upload/bank-statement    Upload CSV → parse transactions
POST /v1/data/fetch               Fetch from AA or existing DB
GET  /v1/data/bank/summary/{id}   Bank account summary
```

### Intelligence (Score)

```
POST /v1/intelligence/score       Compute full credit score
GET  /v1/intelligence/score/{id}  Get latest score
```

**Score response:**

```json
{
  "score": 823,
  "grade": "A",
  "recommended_limit": 8500000,
  "cash_flow_score": 80,
  "payment_discipline_score": 100,
  "gst_compliance_score": 20,
  "revenue_growth_score": 0,
  "business_vintage_score": 0,
  "positive_factors": ["Zero bounce record", "Strong monthly revenue"]
}
```

### Invoices

```
GET    /v1/invoices              List all invoices
POST   /v1/invoices              Create invoice
PUT    /v1/invoices/{id}         Update invoice
POST   /v1/invoices/{id}/mark-paid   Mark as paid
POST   /v1/invoices/{id}/remind  Send WhatsApp reminder
```

### Payments

```
POST /v1/payments/create-link              Razorpay payment link
POST /v1/payments/invoice/{id}/link        Frontend-compatible route
POST /v1/payments/webhook                  Razorpay webhook (auto-score refresh)
GET  /v1/payments/status/{invoice_id}      Payment status
```

### Documents

```
GET /v1/documents/financial-statements/{id}        P&L + Cash Flow JSON
GET /v1/documents/loan-package/{id}/pdf            Complete lender PDF
```

### Lender Portal

```
GET  /v1/lender/pool             Pre-underwritten MSME pool
GET  /v1/lender/business/{id}    Full MSME intelligence profile
POST /v1/lender/approve          Approve loan offer
POST /v1/lender/reject           Reject with reason
```

---

## How The Credit Score Works

The score (300–900) is computed from 5 sub-scores:

| Sub-score | Weight | What it measures |
|-----------|--------|-----------------|
| Cash Flow | 40% | Avg monthly credits, trend, consistency |
| Payment Discipline | 25% | Bounce rate, EMI history, overdue ratio |
| GST Compliance | 20% | Filing rate, turnover match with bank |
| Business Vintage | 10% | Years in operation |
| Revenue Growth | 5% | Month-over-month trend |

**Score updates in real time** — every payment received, invoice paid, or bounce detected triggers an instant recalculation via the Redis event stream.

---

## Lender Integration

Lenders authenticate via API key (not JWT):

```bash
curl -H "X-API-Key: your_lender_key" \
     http://localhost:8000/v1/lender/pool
```

**What lenders get:**
- Live MSME pool filtered by their minimum score threshold
- Pre-underwritten scores — no manual analysis needed
- Real-time alerts when a borrower's health changes
- Sector-level risk analytics
- Early warning system for stressed accounts

**Revenue model:** Lenders pay ₹1Cr/year for the intelligence feed + 0.5–1% origination fee on loans disbursed.

---

## Integrations Setup

### Surepass KYC (Required for onboarding)

1. Sign up at [surepass.io](https://surepass.io)
2. Request sandbox access for: PAN Comprehensive, Corporate GSTIN, Digilocker
3. Add `SUREPASS_API_TOKEN` and `SUREPASS_BASE_URL` to `.env`

**Test PAN:** Use any real PAN number — sandbox accepts live PANs.
**Test GSTIN:** `27AANCR3575R1ZB`

### Razorpay Payments (Required for payment links)

1. Sign up at [razorpay.com](https://razorpay.com)
2. Get test API keys from Dashboard → Settings → API Keys
3. Add to `.env`
4. Add webhook URL: `https://yourdomain.com/v1/payments/webhook`

### Perfios Account Aggregator (For real bank data)

1. Sign up at [perfios.com/aa-developer](https://www.perfios.com/aa-developer)
2. Get sandbox credentials
3. Add `PERFIOS_API_KEY`, `PERFIOS_API_SECRET` to `.env`

**Without Perfios:** Use CSV bank statement upload → `POST /v1/upload/bank-statement`

### GSP API for GST Data

1. Sign up at [mastergst.com](https://www.mastergst.com)
2. Get API credentials
3. Add `GSP_API_KEY`, `GSP_SECRET` to `.env`

**Without GSP:** System scores GST as "pending" (neutral 50/100) — does not block functioning.

---

## First Real MSME — Step by Step

```bash
# 1. Register a business
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "pan": "YOURPAN1A",
    "gstin": "27YOURGSTIN1ZB",
    "business_name": "Your Business Pvt Ltd",
    "owner_name": "Your Name",
    "owner_phone": "9876543210",
    "business_type": "services",
    "city": "Mumbai",
    "state": "Maharashtra"
  }'

# 2. Upload bank statement (CSV)
curl -X POST http://localhost:8000/v1/upload/bank-statement \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@bank_statement.csv" \
  -F "business_id=YOUR_BUSINESS_ID"

# 3. Compute credit score
curl -X POST http://localhost:8000/v1/intelligence/score \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"business_id": "YOUR_BUSINESS_ID"}'

# 4. Download loan package PDF
curl http://localhost:8000/v1/documents/loan-package/YOUR_BUSINESS_ID/pdf \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output loan_package.pdf
```

---

## Bank CSV Format

The system accepts CSV exports from major Indian banks. Expected columns (flexible — auto-detected):

```csv
Date,Narration,Withdrawal,Deposit,Balance
2024-01-15,NEFT-Mehta Fabrics,,500000,1250000
2024-01-16,Supplier Payment-Ram Yarn,180000,,1070000
```

**Supported banks:** HDFC, SBI, ICICI, Axis, Kotak, PNB, Bank of Baroda (and most CSV exports).

---

## Running The Event Stream

For real-time score updates, start the Redis consumer:

```python
# In FastAPI startup (main.py):
import asyncio
from app.agents.event_stream import EventStreamConsumer

@app.on_event("startup")
async def startup():
    asyncio.create_task(EventStreamConsumer().start())
```

Every Razorpay webhook → Redis event → 6 agents → score updated → lender alert sent. Latency: under 2 seconds.

---

## Production Checklist

Before deploying with real money:

- [ ] `encryption.py` — encrypt PAN, bank account numbers at rest
- [ ] Fill Pydantic schemas in `app/schemas/`
- [ ] Write tests in `tests/` (auth, scoring, KYC)
- [ ] Set `APP_ENV=production` — disables debug logs
- [ ] Replace Surepass sandbox with production token
- [ ] Replace Razorpay test keys with live keys
- [ ] RBI FEMA compliance review (for international payments)
- [ ] Data retention policy — PAN data max 90 days
- [ ] SSL certificate + HTTPS for all endpoints
- [ ] Rate limiting on `/v1/kyc/*` endpoints

---

## Phase 2 — International Trade Rail

The next moat: as dollar dominance weakens, Indian MSMEs need multi-currency infrastructure.

```
Sharma Textiles exports to Dubai (AED)
         ↓
CreditBridge captures the invoice
         ↓
AI scores the export transaction
         ↓
Instant working capital: ₹35L against the invoice
         ↓
Dubai pays in AED → system settles in INR
         ↓
FX spread: 0.3% (vs bank's 2-3%)
```

**Files to build:**
- `multi_currency_rail.py`
- `fx_engine.py` — real-time FX rates + settlement
- `export_invoice_finance.py` — receivables factoring
- `rbi_fema_compliance.py` — regulatory wrapper

**Requires:** RBI FEMA license, correspondent banking relationships, AD-1 category bank partnership.

---

## Competitive Position

| | Traditional Bank | Existing Fintech | CreditBridge |
|---|---|---|---|
| Underwriting time | 2-3 weeks | 3-5 days | Hours |
| Data source | Documents | Credit bureau | Live transactions |
| Score updates | Monthly | Weekly | Real-time |
| NPA prediction | Historical | Static model | Predictive AI |
| Lender cost | High | Medium | Near zero |
| MSME effort | High (docs) | Medium | Low (CSV/AA) |

---

## Scale Targets

| Year | MSMEs | Loan Volume | Revenue | Valuation |
|------|-------|-------------|---------|-----------|
| 1 | 1,000 | ₹100Cr | ₹1-2Cr | — |
| 3 | 50,000 | ₹10,000Cr | ₹100-200Cr | $120M |
| 5 | 5,00,000 | ₹1,00,000Cr | ₹1,000Cr+ | $1-2B |
| 10 | 3Cr | $100B | $1-2B | $10-20B |

---

## Contributing

This is a private repository. Internal team guidelines:

**Branch naming:**
```
feature/kyc-aadhaar-otp
fix/payment-link-404
infra/redis-event-stream
```

**Commit style:**
```
feat: add Perfios AA real bank feed
fix: remove mock data from aa_service.py
docs: update API reference for /v1/kyc/pan
```

**Before pushing:**
```bash
cd backend
python -m pytest tests/
cd frontend
npm run build
```

---

## License

Private and confidential. All rights reserved.

© 2025 CreditBridge Technologies Pvt Ltd

---

## Contact

**Anand Chuahan** — Founder  
Email: mindsux44@gmail.com  
Phone: +91-7400421710

> *"Every $10T company started with one real customer. Amazon: 1 book. Stripe: 1 payment. CreditBridge: 1 real MSME, 1 real loan."*