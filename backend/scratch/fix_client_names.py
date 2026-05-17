import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load env from root dir
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "smart_invoice")

async def migrate_client_names():
    if not MONGODB_URI:
        print("❌ MONGODB_URI not found in environment")
        return

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    clients_coll = db["clients"]

    print("🔍 Searching for clients with name '1'...")
    cursor = clients_coll.find({"name": "1"})
    count = 0

    async for doc in cursor:
        email = doc.get("email")
        if email and "@" in email:
            # Smart extract name from email
            new_name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
            print(f"✅ Updating {email}: '1' -> '{new_name}'")
            await clients_coll.update_one(
                {"_id": doc["_id"]},
                {"$set": {"name": new_name}}
            )
            count += 1
        else:
            print(f"⚠️ Cannot fix client {doc.get('_id')} (no valid email)")

    print(f"\n🎉 Migration complete. Fixed {count} clients.")

if __name__ == "__main__":
    asyncio.run(migrate_client_names())
