import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def force_approve_user(email):
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    users = db.users
    
    user = await users.find_one({"email": email})
    if not user:
        print(f"❌ User {email} not found.")
        return

    await users.update_one(
        {"email": email},
        {"$set": {"status": "approved", "is_active": True}}
    )
    print(f"✅ User {email} has been FORCED to APPROVED status.")
    
    # Also ensure the Admin is approved
    admin_email = "admin@example.com"
    await users.update_one(
        {"email": admin_email},
        {"$set": {"status": "approved", "is_active": True}}
    )
    print(f"✅ Admin {admin_email} has been verified as APPROVED.")
    
    client.close()

if __name__ == "__main__":
    email_to_approve = "user@example.com"
    asyncio.run(force_approve_user(email_to_approve))
