import motor.motor_asyncio
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('DB_NAME')]
    users = db['users']
    u = await users.find_one({'email': 'admin@example.com'})
    print(f"USER: {u}")
    client.close()

if __name__ == "__main__":
    asyncio.run(run())
