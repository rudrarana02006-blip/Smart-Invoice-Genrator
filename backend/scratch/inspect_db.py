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
    
    print("\n--- COLLECTIONS ---")
    collections = await db.list_collection_names()
    print(collections)
    
    for coll_name in collections:
        count = await db[coll_name].count_documents({})
        print(f"\nCollection: {coll_name} ({count} documents)")
        cursor = db[coll_name].find().limit(5)
        async for doc in cursor:
            # Mask some fields for privacy if needed, but this is a scratch script
            print(f"  {doc}")

    print("\n--- UNIQUE ORG_IDs ---")
    orgs = await db["users"].distinct("org_id")
    print(f"Users Org IDs: {orgs}")
    
    client_orgs = await db["clients"].distinct("org_id")
    print(f"Clients Org IDs: {client_orgs}")

    invoice_orgs = await db["invoices"].distinct("org_id")
    print(f"Invoices Org IDs: {invoice_orgs}")

if __name__ == "__main__":
    asyncio.run(inspect_db())
