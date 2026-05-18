import asyncio
import os
import sys
from bson import ObjectId

# Setup path so imports work
sys.path.append(os.getcwd())

from database import get_user_collection, connect_to_mongo, close_mongo_connection

async def check():
    await connect_to_mongo()
    users = get_user_collection()
    current_user = await users.find_one({"role": "admin"})
    if not current_user:
        current_user = {"email": "admin@devleds.com", "role": "admin", "org_id": "6a02f0695760fb27f089ff0b"}
    
    current_user["_id"] = str(current_user["_id"])
    
    # Run the exact permission check from design.py
    is_admin = current_user.get("role") == "admin"
    org_id = current_user.get("org_id")
    
    print(f"User: {current_user.get('email')}")
    print(f"Role: {current_user.get('role')} (is_admin: {is_admin})")
    print(f"Org ID: {org_id}")
    
    if not org_id:
        print("ERROR: Organization ID missing from profile.")
        return
        
    is_independent = org_id == str(current_user.get("_id", ""))
    print(f"Is Independent: {is_independent}")
    
    if not (is_admin or is_independent):
        print("ERROR: Only Admins or Independent users can set custom formats. (403 Forbidden)")
    else:
        print("SUCCESS: Permission check passed!")
        
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check())
