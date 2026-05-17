from fastapi import APIRouter, HTTPException
import httpx
from cachetools import TTLCache

router = APIRouter()

# Simple cache to avoid hitting the API too hard (TTL 1 hour)
rates_cache = TTLCache(maxsize=1, ttl=3600)

@router.get("/rates")
async def get_exchange_rates():
    """
    Fetches latest exchange rates from Frankfurter API.
    Cached for 1 hour.
    """
    if "latest" in rates_cache:
        return rates_cache["latest"]
        
    try:
        async with httpx.AsyncClient() as client:
            # We use INR as base for convenience, but the frontend can calculate between any
            response = await client.get("https://www.frankfurter.app/latest?from=INR")
            response.raise_for_status()
            data = response.json()
            rates_cache["latest"] = data
            return data
    except Exception as e:
        print(f"EXCHANGE RATE ERROR: {e}")
        # Fallback to some static common rates if API is down
        fallback = {
            "amount": 1.0,
            "base": "INR",
            "date": "2024-05-15",
            "rates": {
                "USD": 0.012,
                "EUR": 0.011,
                "GBP": 0.009,
                "AED": 0.044,
                "CAD": 0.016,
                "AUD": 0.018,
                "JPY": 1.85,
                "SGD": 0.016
            }
        }
        return fallback
