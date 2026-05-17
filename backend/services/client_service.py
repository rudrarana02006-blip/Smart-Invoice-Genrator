"""
Client Service — Business logic for client CRUD operations.
"""

from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional

from database import get_db
from models.client import ClientCreate, ClientUpdate, ClientInDB

def get_client_collection():
    return get_db()["clients"]

async def create_client(client_data: ClientCreate, current_user: dict) -> dict:
    clients = get_client_collection()
    client_dict = client_data.model_dump()
    
    org_id = current_user.get("org_id")
    client_dict["org_id"] = org_id
    client_dict["created_by"] = current_user.get("email")
    client_dict["created_at"] = datetime.now(timezone.utc)
    client_dict["updated_at"] = client_dict["created_at"]
    
    result = await clients.insert_one(client_dict)
    client_dict["_id"] = str(result.inserted_id)
    return client_dict

async def get_all_clients(current_user: dict) -> List[dict]:
    clients = get_client_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    if current_user.get("role") == UserRole.ADMIN:
        query = {"org_id": org_id}
    else:
        query = {"org_id": org_id, "created_by": current_user["email"]}
        
    cursor = clients.find(query).sort("name", 1)
    return [{**doc, "_id": str(doc["_id"])} async for doc in cursor]

async def get_client(client_id: str, current_user: dict) -> Optional[dict]:
    clients = get_client_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    query = {"_id": ObjectId(client_id), "org_id": org_id}
    if current_user.get("role") != UserRole.ADMIN:
        query["created_by"] = current_user["email"]
        
    client = await clients.find_one(query)
    if client:
        client["_id"] = str(client["_id"])
    return client

async def update_client(client_id: str, current_user: dict, update_data: ClientUpdate) -> Optional[dict]:
    clients = get_client_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    query = {"_id": ObjectId(client_id), "org_id": org_id}
    if current_user.get("role") != UserRole.ADMIN:
        query["created_by"] = current_user["email"]
        
    existing = await clients.find_one(query)
    if not existing:
        return None
        
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    await clients.update_one(query, {"$set": update_dict})
    return await get_client(client_id, current_user)

async def delete_client(client_id: str, current_user: dict) -> bool:
    clients = get_client_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    query = {"_id": ObjectId(client_id), "org_id": org_id}
    if current_user.get("role") != UserRole.ADMIN:
        query["created_by"] = current_user["email"]
        
    result = await clients.delete_one(query)
    return result.deleted_count > 0

async def ensure_client_exists(client_name: str, client_email: str, client_address: str, current_user: dict):
    """Checks if a client exists for the organization; if not, creates them."""
    clients = get_client_collection()
    org_id = current_user.get("org_id")
    
    # Smart Fix for placeholder names like "1"
    if client_name.strip() in ["1", "", "null", "undefined"] and client_email:
        # Extract name from email (e.g. "john.doe" from "john.doe@gmail.com")
        client_name = client_email.split('@')[0].replace('.', ' ').replace('_', ' ').title()

    # Check by email and org_id
    existing = await clients.find_one({"email": client_email, "org_id": org_id})
    if not existing:
        client_doc = {
            "name": client_name,
            "email": client_email,
            "address": client_address,
            "org_id": org_id,
            "created_by": current_user.get("email"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await clients.insert_one(client_doc)
        print(f"DEBUG: Auto-saved new client: {client_name} for org {org_id}")
    else:
        # Optionally update address if it was blank before
        if not existing.get("address") and client_address:
            await clients.update_one({"_id": existing["_id"]}, {"$set": {"address": client_address, "updated_at": datetime.now(timezone.utc)}})
