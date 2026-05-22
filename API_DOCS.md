# CreditBridge API Documentation

Base URL: `http://localhost:8000/v1`  
Interactive docs: `http://localhost:8000/docs`  
Auth: JWT Bearer token (MSME) | X-API-Key header (Lender)

---

## Authentication

### Register MSME
`POST /v1/auth/register`

```json
{
  "pan": "ABCDE1234F",
  "gstin": "27ABCDE1234F1Z5",
  "business_name": "Sharma Textiles Pvt Ltd",
  "owner_name": "Rajesh Sharma",
  "owner_phone": "9876543210",
  "owner_email": "rajesh@sharma.com",
  "business_type": "textile",
  "city": "Surat",
  "state": "Gujarat"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "business_id": "uuid",
  "message": "Registration successful"
}
```

### Login
`POST /v1/auth/login`

```json
{ "phone": "9876543210" }
```

---

## KYC

> All KYC endpoints call Surepass sandbox/production.
> Sandbox URL: `https://sandbox.surepass.io`

### PAN Comprehensive Verify
`POST /v1/kyc/pan`

```json
{ "pan_number": "ABCDE1234F" }
```

**Response:**
```json
{
  "verified": true,
  "pan": "ABCDE1234F",
  "full_name": "RAJESH SHARMA",
  "dob": "1985-03-15",
  "gender": "M",
  "category": "person",
  "aadhaar_linked": true,
  "masked_aadhaar": "XXXXXXXX5272",
  "email": "RA*****MA@GMAIL.COM",
  "phone_number": "98XXXXXX10",
  "address": {
    "city": "Surat",
    "state": "Gujarat",
    "full": "123 Main St, Surat, Gujarat"
  }
}
```

### GSTIN Verify
`POST /v1/kyc/gstin`

```json
{ "gstin": "27AANCR3575R1ZB" }
```

**Response:**
```json
{
  "verified": true,
  "gstin": "27AANCR3575R1ZB",
  "business_name": "SHARMA TEXTILES PVT LTD",
  "legal_name": "RAJESH SHARMA",
  "gstin_status": "Active",
  "registration_date": "2020-01-15",
  "business_type": "Private Limited Company",
  "taxpayer_type": "Regular",
  "state_jurisdiction": "State - Maharashtra",
  "aadhaar_validation": "Yes",
  "address": "123 Industrial Area, Surat, Gujarat"
}
```

### Combined MSME KYC
`POST /v1/kyc/msme`

```json
{
  "pan": "ABCDE1234F",
  "gstin": "27AANCR3575R1ZB"
}
```

**Response:**
```json
{
  "kyc_passed": true,
  "name_match": true,
  "kyc_score": 100,
  "pan": { "...pan fields..." },
  "gstin": { "...gstin fields..." }
}
```

---

## Bank Data

### Upload Bank Statement CSV
`POST /v1/upload/bank-statement`

Content-Type: `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `file` | File (CSV/XLSX) | Yes |
| `business_id` | string | Yes |

**CSV format expected:**
```
Date, Narration, Withdrawal, Deposit, Balance
2024-01-15, NEFT-Mehta Fabrics, , 500000, 1250000
```

**Response:**
```json
{
  "status": "success",
  "transactions_imported": 84,
  "date_range": "2023-01-01 to 2024-01-15",
  "total_credits": 45600000,
  "total_debits": 27360000
}
```

### Fetch / Confirm Bank Data
`POST /v1/data/fetch`

```json
{ "business_id": "uuid" }
```

**Response (data exists):**
```json
{
  "status": "success",
  "source": "database",
  "transactions_stored": 84,
  "account": {
    "bank_name": "HDFC Bank",
    "masked_account": "XXXX4521",
    "avg_monthly_credits": 3800000,
    "avg_monthly_balance": 1200000,
    "bounce_count_12m": 0
  },
  "next_step": "POST /v1/intelligence/score"
}
```

**Response (no data):**
```json
{
  "error": "no_bank_data",
  "message": "Bank data nahi hai. CSV upload karo.",
  "upload_endpoint": "POST /v1/upload/bank-statement"
}
```

---

## Credit Intelligence

### Compute Score
`POST /v1/intelligence/score`

```json
{ "business_id": "uuid" }
```

**Response:**
```json
{
  "score": 823,
  "grade": "A",
  "recommended_limit": 8500000,
  "avg_monthly_revenue": 3800000,
  "cash_flow_score": 80,
  "payment_discipline_score": 100,
  "gst_compliance_score": 20,
  "revenue_growth_score": 0,
  "business_vintage_score": 0,
  "positive_factors": [
    "Zero bounce record — excellent payment discipline",
    "Strong monthly revenue above ₹30L",
    "Consistent monthly cash flows"
  ],
  "risk_factors": [
    "GST data not yet connected",
    "Limited vintage data"
  ],
  "loan_offers": [
    {
      "lender": "Lendingkart NBFC",
      "amount": 7500000,
      "rate": 13.5,
      "tenure": 12,
      "featured": true
    }
  ]
}
```

### Get Latest Score
`GET /v1/intelligence/score/{business_id}`

---

## Invoices

### List Invoices
`GET /v1/invoices`

**Query params:** `status`, `party_type`, `page`, `limit`

### Create Invoice
`POST /v1/invoices`

```json
{
  "invoice_number": "INV-2024-047",
  "party_name": "Mehta Fabrics Pvt Ltd",
  "party_type": "customer",
  "amount": 500000,
  "due_date": "2024-02-10",
  "invoice_date": "2024-01-10",
  "description": "Cotton fabric supply — Jan batch"
}
```

### Mark Invoice Paid
`POST /v1/invoices/{id}/mark-paid`

> Triggers score refresh via Redis event stream.

### Send WhatsApp Reminder
`POST /v1/invoices/{id}/remind`

---

## Payments

### Create Payment Link
`POST /v1/payments/create-link`

```json
{
  "business_id": "uuid",
  "invoice_id": "uuid"
}
```

**Response:**
```json
{
  "invoice_number": "INV-2024-047",
  "party_name": "Mehta Fabrics",
  "amount_due": 500000,
  "payment_link": "https://rzp.io/l/abc123",
  "message": "Share this link with Mehta Fabrics to collect payment"
}
```

### Razorpay Webhook
`POST /v1/payments/webhook`

> Called automatically by Razorpay when buyer pays.
> System marks invoice as paid + fires score refresh event.

**Required header:** `X-Razorpay-Signature`

---

## Documents

### Financial Statements
`GET /v1/documents/financial-statements/{business_id}`

**Response:**
```json
{
  "business_name": "Sharma Textiles Pvt Ltd",
  "period": "May 2023 – Apr 2024",
  "pl": {
    "revenue": 45600000,
    "cogs": 27360000,
    "gross_profit": 18240000,
    "gross_margin": 40.0,
    "ebitda": 9120000,
    "ebitda_margin": 20.0,
    "monthly": [...]
  },
  "cash_flow": {
    "opening_balance": 2500000,
    "total_inflows": 45600000,
    "total_outflows": 27360000,
    "net_cash_flow": 18240000,
    "working_capital": 18200000,
    "monthly": [...]
  }
}
```

### Loan Package PDF
`GET /v1/documents/loan-package/{business_id}/pdf`

Returns a complete lender-ready PDF containing:
- KYC verification summary
- 12-month P&L statement
- Cash flow statement
- Credit score breakdown
- Loan offers

---

## Lender Portal

> Authentication: `X-API-Key: your_lender_key` header

### Get MSME Pool
`GET /v1/lender/pool`

**Query params:** `min_score` (default: 650), `page`, `limit`

**Response:**
```json
{
  "pool": [
    {
      "business_id": "uuid",
      "business_name": "Sharma Textiles",
      "score": 823,
      "grade": "A",
      "recommended_limit": 8500000,
      "avg_monthly_revenue": 3800000,
      "score_updated": "2024-01-15",
      "loan_health": "GREEN"
    }
  ],
  "total": 141
}
```

### Get Business Intelligence
`GET /v1/lender/business/{business_id}`

Returns complete MSME profile: score breakdown, financials, invoice health, buyer reliability scores, cash flow forecast.

### Approve Loan Offer
`POST /v1/lender/approve`

```json
{
  "business_id": "uuid",
  "amount": 7500000,
  "rate": 13.5,
  "tenure_months": 12,
  "lender_name": "Lendingkart NBFC"
}
```

---

## Consent / AA Flow

### Initiate AA Consent
`POST /v1/consent/initiate`

```json
{
  "business_id": "uuid",
  "phone": "9876543210"
}
```

**If Perfios configured:**
```json
{
  "consent_id": "uuid",
  "redirect_url": "https://sandbox.perfios.com/consent/...",
  "source": "perfios_aa"
}
```

**If not configured (use CSV instead):**
```json
{
  "status": "csv_required",
  "upload_endpoint": "POST /v1/upload/bank-statement",
  "instructions": "Bank statement CSV upload karo"
}
```

### Check Consent Status
`GET /v1/consent/status/{business_id}`

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request — check request body |
| 401 | Invalid or missing token |
| 404 | Resource not found |
| 422 | Validation failed (KYC, amount limits) |
| 500 | Server error — check logs |

**KYC-specific errors:**
```json
{ "detail": "Invalid PAN" }
{ "detail": "Your token(signature) is invalid" }
{ "detail": "GSTIN verification failed" }
```

---

## Rate Limits

| Endpoint group | Limit |
|----------------|-------|
| `/v1/kyc/*` | 100 req/hour per API key |
| `/v1/intelligence/score` | 50 req/hour per business |
| `/v1/payments/*` | No limit (webhook driven) |
| All others | 1000 req/hour |

---

## Webhook Events

### payment_link.paid (from Razorpay)
```json
{
  "event": "payment_link.paid",
  "payload": {
    "payment_link": {
      "entity": {
        "amount": 50000000,
        "notes": {
          "business_id": "uuid",
          "invoice_number": "INV-2024-047"
        }
      }
    }
  }
}
```

**What happens:**
1. Invoice marked as paid
2. `publish_event_sync()` fires to Redis
3. `EventStreamConsumer` picks up event
4. 6 agents run → score updated
5. Lender alert pushed if score changes significantly