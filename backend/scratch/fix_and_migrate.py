import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def fix_indexes_and_migrate():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    print(f"🔧 Fixing indexes on: {db_name}...")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    coll = db["clients"]
    
    # 1. Drop the restrictive global email index
    try:
        await coll.drop_index("email_1")
        print("✅ Dropped global unique email index.")
    except Exception as e:
        print(f"ℹ️ Could not drop email_1 index (it might not exist): {e}")

    # 2. Create the proper multi-tenant unique index
    try:
        await coll.create_index([("email", 1), ("org_id", 1)], unique=True)
        print("✅ Created proper compound unique index (email + org_id).")
    except Exception as e:
        print(f"❌ Failed to create compound index: {e}")

    # 3. Re-run migration logic
    print("\n🚀 Re-running migration...")
    invoices_coll = db["invoices"]
    cursor = invoices_coll.find({})
    async for inv in cursor:
        client_name = inv.get("client_name")
        client_email = inv.get("client_email")
        client_address = inv.get("client_address")
        org_id = inv.get("org_id")
        created_by = inv.get("created_by")
        
        if not client_email or not org_id: continue
        
        try:
            await coll.update_one(
                {"email": client_email, "org_id": org_id},
                {"$setOnInsert": {
                    "name": client_name,
                    "email": client_email,
                    "address": client_address,
                    "org_id": org_id,
                    "created_by": created_by,
                    "created_at": inv.get("created_at"),
                    "updated_at": inv.get("created_at")
                }},
                upsert=True
            )
            print(f"Synced: {client_name}")
        except Exception as e:
            print(f"Skipped {client_name}: {e}")

    print("\n✨ All done!")

if __name__ == "__main__":
    asyncio.run(fix_indexes_and_migrate())
