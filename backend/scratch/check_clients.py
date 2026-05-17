import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

async def check():
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    clients = db["clients"]
    
    print("Listing all clients in DB:")
    cursor = clients.find({})
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Name: {doc.get('name')} | Email: {doc.get('email')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check())
