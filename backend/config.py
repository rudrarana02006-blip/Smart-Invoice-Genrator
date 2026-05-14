"""
Configuration module — loads environment variables using pydantic-settings.
All secrets and app settings are centralized here.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Devleds Generator"
    DEBUG: bool = True

    # Database
    MONGODB_URI: str
    DB_NAME: str = "smart_invoice"

    # AI API
    GEMINI_API_KEY: str

    # Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Geocoding
    GOOGLE_MAPS_API_KEY: str = ""
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "invoice@2026"

    # Email Configuration
    # SMTP Settings (For AI Mailer)
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM_NAME: str = "Devleds Generator"
    MAIL_FROM_EMAIL: Optional[str] = None
    ADMIN_EMAIL: Optional[str] = None

    class Config:
        import os
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False

# Instantiate settings to be used globally
settings = Settings()
