import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def test_connection():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    
    print(f"🔍 Attempting to connect to: {db_name}")
    
    try:
        client = AsyncIOMotorClient(uri)
        # The ismaster command is cheap and does not require auth.
        await client.admin.command('ismaster')
        
        # Now try to list collections to verify auth
        db = client[db_name]
        collections = await db.list_collection_names()
        
        print("✅ CONNECTION SUCCESSFUL!")
        print(f"📦 Found {len(collections)} collections: {collections}")
        
    except Exception as e:
        print("❌ CONNECTION FAILED!")
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
