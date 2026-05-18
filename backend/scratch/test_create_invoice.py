import asyncio
import os
import requests
from dotenv import load_dotenv

# We need a token to test the API. 
# But I can test the SERVICE directly which is faster.

from motor.motor_asyncio import AsyncIOMotorClient
from services.invoice_service import create_invoice
from models.invoice import InvoiceCreate

load_dotenv()

async def test_create():
    # Mock current_user
    current_user = {
        "email": "admin@devleds.com",
        "org_id": "6a02f0695760fb27f089ff0b",
        "role": "admin",
        "status": "approved"
    }
    
    invoice_data = {
        "client_name": "Test Client Today",
        "client_email": "test_today@example.com",
        "client_address": "Mumbai",
        "due_date": "2026-06-14T00:00:00Z",
        "items": [
            {"description": "Test Item", "quantity": 1, "rate": 100}
        ]
    }
    
    try:
        from database import connect_to_mongo
        await connect_to_mongo()
        
        invoice_obj = InvoiceCreate(**invoice_data)
        result = await create_invoice(invoice_obj, current_user)
        print(f"✅ Success! Created Invoice ID: {result['_id']}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # We need to set up the environment so imports work
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(test_create())
