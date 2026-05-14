import asyncio
from database import get_user_collection, connect_to_mongo, close_mongo_connection

async def check():
    await connect_to_mongo()
    users = get_user_collection()
    cursor = users.find({})
    async for u in cursor:
        print(f"Email: {u.get('email')} | Role: {u.get('role')} | Status: {u.get('status')}")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check())
