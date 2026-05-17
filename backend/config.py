"""
Configuration module — loads environment variables using pydantic-settings.
All secrets and app settings are centralized here.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Smart Invoice Generator"
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
    MAIL_FROM_NAME: str = "Smart Invoice Generator"
    MAIL_FROM_EMAIL: Optional[str] = None
    ADMIN_EMAIL: Optional[str] = None
    USER_EMAIL: Optional[str] = None

    class Config:
        import os
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False

# Instantiate settings to be used globally
settings = Settings()

# Dynamic Model Discovery Helper (Global)
def get_gemini_model(vision: bool = False):
    """
    Queries the Gemini API to discover authorized models for the current key.
    Prevents 404 errors by picking names dynamically.
    """
    import google.generativeai as genai
    try:
        if not settings.GEMINI_API_KEY or "your" in settings.GEMINI_API_KEY.lower():
            return None
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # List all models authorized for this specific key
        available = [m.name.replace('models/', '') for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods]
        
        if not available:
            # Fallback to absolute basics if list fails or is empty
            return genai.GenerativeModel('gemini-pro')

        # Priority Selection
        if vision:
            for preferred in ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro-vision']:
                if preferred in available: return genai.GenerativeModel(preferred)
        else:
            for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
                if preferred in available: return genai.GenerativeModel(preferred)
        
        # Pick the first available if no preferred match
        return genai.GenerativeModel(available[0])
    except Exception as e:
        print(f"⚠️ GEMINI DISCOVERY FAILED: {e}")
        # Final safety net
        try:
            return genai.GenerativeModel('gemini-pro')
        except:
            return None
