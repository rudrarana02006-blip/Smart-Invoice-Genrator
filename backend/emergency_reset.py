import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone

import os
from dotenv import load_dotenv

load_dotenv()

# LOAD FROM ENV FOR SECURITY
MONGODB_URI = os.getenv("MONGODB_URI", "your_mongodb_uri_here")
EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
NEW_PASSWORD = "12345678"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_password():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    users = db.users
    
    hashed_password = pwd_context.hash(NEW_PASSWORD)
    
    result = await users.update_one(
        {"email": EMAIL},
        {
            "$set": {
                "hashed_password": hashed_password,
                "is_verified": True,
                "token_version": 1,
                "updated_at": datetime.now(timezone.utc)
            },
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc),
                "is_active": True
            }
        },
        upsert=True
    )
    
    if result.upserted_id:
        print(f"User {EMAIL} created with password: {NEW_PASSWORD}")
    else:
        print(f"User {EMAIL} password reset to: {NEW_PASSWORD}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_password())
