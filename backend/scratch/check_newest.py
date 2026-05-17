import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_newest():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    print("--- 5 NEWEST INVOICES ---")
    cursor = db["invoices"].find().sort("created_at", -1).limit(5)
    async for inv in cursor:
        print(f"Name: {inv.get('client_name')} | Created: {inv.get('created_at')} | Org: {inv.get('org_id')}")

if __name__ == "__main__":
    asyncio.run(check_newest())
