from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
from pathlib import Path

# This finds the .env file no matter where alembic runs from
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    model_config = ConfigDict(extra="ignore", env_file=str(ENV_FILE))
    APP_ENV: str = "development"
    APP_BASE_URL: str = "http://localhost:8000"
    SECRET_KEY: str 
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    JWT_REFRESH_EXPIRATION_DAYS: int = 7
    
    #database settings
    DATABASE_URL: str
    REDIS_URL : str = "redis://localhost:6379"

    # Razorpay API
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    
    SUREPASS_API_TOKEN: Optional[str] = None
    SUREPASS_BASE_URL: str = "https://sandbox.surepass.io"

    SETU_CLIENT_ID: Optional[str] = None
    SETU_CLIENT_SECRET: Optional[str] = None
    SETU_PRODUCT_INSTANCE_ID: Optional[str] = None
    SETU_BASE_URL : str = "https://fiu-sandbox.setu.co"
    SETU_WEBHOOK_URL : Optional[str] = None
    
    # GSTIN API
    GSTN_API_KEY: Optional[str] = None
    GSTN_BASE_URL: str = "https://api.gstn.org.in"

    # ai api

    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPEN_API_KEY: Optional[str] = None  # backward compatibility
    ENCRYPTION_KEY : str = "your-encryption-key"

    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_WHATSAPP_FROM: Optional[str] = None
    
settings = Settings()
