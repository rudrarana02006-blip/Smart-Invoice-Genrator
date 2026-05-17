import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def inspect_db():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    print(f"Connecting to: {uri[:20]}...")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    admin_email = "apnekaamsemtlbrkh@gmail.com"
    user = await db["users"].find_one({"email": admin_email})
    if not user:
        print(f"User {admin_email} not found")
        return
    
    org_id = user.get("org_id")
    print(f"User Org ID: {org_id}")
    
    print("\n--- INVOICES FOR THIS ORG ---")
    cursor = db["invoices"].find({"org_id": org_id})
    async for inv in cursor:
        print(f"ID: {inv['_id']} | Client: {inv.get('client_name')} | Address: {inv.get('client_address')} | Total: {inv.get('grand_total')}")

    print("\n--- CLIENTS FOR THIS ORG ---")
    cursor = db["clients"].find({"org_id": org_id})
    async for cli in cursor:
        print(f"ID: {cli['_id']} | Name: {cli.get('name')} | Address: {cli.get('address')}")

if __name__ == "__main__":
    asyncio.run(inspect_db())
