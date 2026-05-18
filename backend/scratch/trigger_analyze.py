import asyncio
import os
import sys
import httpx
from datetime import timedelta

# Setup path so imports work
sys.path.append(os.getcwd())

from database import get_user_collection, connect_to_mongo, close_mongo_connection
from auth import create_access_token

async def test():
    await connect_to_mongo()
    users = get_user_collection()
    user = await users.find_one({"role": "admin"})
    if not user:
        user = {"email": "admin@devleds.com", "token_version": 1, "role": "admin"}
    
    # Generate token
    token = create_access_token(
        data={
            "sub": user["email"],
            "v": user.get("token_version", 1),
            "role": user.get("role")
        },
        expires_delta=timedelta(minutes=10)
    )
    print("Generated token:", token)
    await close_mongo_connection()

    # Make post request using httpx
    # Create a small dummy png image
    dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with httpx.AsyncClient() as client:
        files = {
            "file": ("invoice.png", dummy_png, "image/png")
        }
        response = await client.post("http://localhost:8000/api/design/analyze", headers=headers, files=files, timeout=60.0)
        print("Response status code:", response.status_code)
        print("Response body:", response.text)

if __name__ == "__main__":
    asyncio.run(test())
