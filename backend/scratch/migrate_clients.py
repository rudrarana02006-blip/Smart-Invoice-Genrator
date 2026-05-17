import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

async def migrate_clients():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    print(f"🚀 Starting Client Migration on: {db_name}...")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    invoices_coll = db["invoices"]
    clients_coll = db["clients"]
    
    # Get all invoices
    cursor = invoices_coll.find({})
    invoices = await cursor.to_list(length=None)
    
    saved_count = 0
    skipped_count = 0
    
    for inv in invoices:
        client_name = inv.get("client_name")
        client_email = inv.get("client_email")
        client_address = inv.get("client_address")
        org_id = inv.get("org_id")
        created_by = inv.get("created_by")
        
        if not client_email or not org_id:
            continue
            
        # Check if already in clients
        existing = await clients_coll.find_one({"email": client_email, "org_id": org_id})
        
        if not existing:
            client_doc = {
                "name": client_name,
                "email": client_email,
                "address": client_address,
                "org_id": org_id,
                "created_by": created_by,
                "created_at": inv.get("created_at", datetime.now(timezone.utc)),
                "updated_at": datetime.now(timezone.utc)
            }
            await clients_coll.insert_one(client_doc)
            print(f"✅ Added client: {client_name} ({client_email})")
            saved_count += 1
        else:
            skipped_count += 1
            
    print(f"\n✨ Migration Complete!")
    print(f"   - New clients saved: {saved_count}")
    print(f"   - Already existed: {skipped_count}")

if __name__ == "__main__":
    asyncio.run(migrate_clients())
