import asyncio
from database import get_user_collection, connect_to_mongo, close_mongo_connection
from bson import ObjectId

async def check():
    await connect_to_mongo()
    users = get_user_collection()
    u = await users.find_one({"role": "admin"})
    if not u:
        u = {"email": "admin@devleds.com", "role": "admin"}
    print("User document:")
    print(u)
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check())
