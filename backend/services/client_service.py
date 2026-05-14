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
    
    cursor = clients.find({"org_id": org_id}).sort("name", 1)
    return [{**doc, "_id": str(doc["_id"])} async for doc in cursor]

async def get_client(client_id: str, current_user: dict) -> Optional[dict]:
    clients = get_client_collection()
    org_id = current_user.get("org_id")
    
    client = await clients.find_one({"_id": ObjectId(client_id), "org_id": org_id})
    if client:
        client["_id"] = str(client["_id"])
    return client

async def update_client(client_id: str, current_user: dict, update_data: ClientUpdate) -> Optional[dict]:
    clients = get_client_collection()
    org_id = current_user.get("org_id")
    
    query = {"_id": ObjectId(client_id), "org_id": org_id}
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
    
    result = await clients.delete_one({"_id": ObjectId(client_id), "org_id": org_id})
    return result.deleted_count > 0
