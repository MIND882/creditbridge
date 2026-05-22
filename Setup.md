# Developer Setup Guide

## Local Development — Full Stack

### 1. Install dependencies

**Mac/Linux:**
```bash
brew install postgresql redis python@3.11 node

# Start services
brew services start postgresql
brew services start redis
```

**Windows:**
- PostgreSQL: https://www.postgresql.org/download/windows/
- Redis: https://redis.io/docs/install/install-redis/install-redis-on-windows/
- Python 3.11: https://www.python.org/downloads/

### 2. Create database

```bash
psql -U postgres
CREATE DATABASE creditbridge;
CREATE USER creditbridge_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE creditbridge TO creditbridge_user;
\q
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Fill in your values
alembic upgrade head
uvicorn app.main:app --reload
```

**Verify backend:**
```bash
curl http://localhost:8000/health
# → {"status": "ok"}

curl http://localhost:8000/v1/kyc/health
# → {"status": "ok", "provider": "Surepass", ...}
```

### 4. Frontends

```bash
# Terminal 1 — MSME App
cd frontend
npm install
npm run dev   # → localhost:5173

# Terminal 2 — Lender Portal
cd frontend-lender
npm install
npm run dev   # → localhost:5174
```

### 5. Redis event stream (optional for real-time scoring)

The event stream starts automatically with FastAPI via the `startup` event.
To verify it's running, check logs for:
```
[EventStream] Consumer started — waiting for events...
```

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v

# Specific test
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_intelligence.py -v
```

---

## Adding a New API Endpoint

1. Create route in `backend/app/api/v1/your_route.py`
2. Register in `backend/app/main.py`:
```python
from app.api.v1 import your_route
app.include_router(your_route.router, prefix="/v1/your-prefix")
```
3. Add Pydantic schema in `backend/app/schemas/`
4. Write test in `backend/tests/`

---

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `SECRET_KEY` | ✅ | JWT signing key (random 32+ chars) |
| `SUREPASS_API_TOKEN` | ✅ | Surepass JWT token |
| `SUREPASS_BASE_URL` | ✅ | Sandbox or production URL |
| `RAZORPAY_KEY_ID` | ✅ | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | ✅ | Razorpay secret |
| `PERFIOS_API_KEY` | Optional | Account Aggregator (use CSV without) |
| `GSP_API_KEY` | Optional | GST data (neutral score without) |
| `TWILIO_ACCOUNT_SID` | Optional | WhatsApp notifications |

---

## Common Issues

**`ModuleNotFoundError: No module named 'app'`**
```bash
# Run from backend/ directory
cd backend
uvicorn app.main:app --reload
```

**`SUREPASS_API_TOKEN` is None**
```bash
# Check .env is in backend/ folder (not backend/app/)
ls backend/.env
```

**Alembic migration fails**
```bash
# Reset and redo
alembic downgrade base
alembic upgrade head
```

**Redis connection refused**
```bash
# Start Redis
redis-server

# Or on Windows
redis-server.exe
```

**Frontend can't reach backend (CORS error)**
```bash
# In backend/app/main.py, check CORS origins include:
# http://localhost:5173 (MSME)
# http://localhost:5174 (Lender)
```