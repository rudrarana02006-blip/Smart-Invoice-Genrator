"""
Client Routes — Full CRUD for client management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from auth import get_approved_user
from models.client import ClientCreate, ClientUpdate
from services import client_service

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_client(client: ClientCreate, current_user: dict = Depends(get_approved_user)):
    """Create a new client."""
    return await client_service.create_client(client, current_user)

@router.get("/")
async def list_all_clients(current_user: dict = Depends(get_approved_user)):
    """List all clients for the organization."""
    return await client_service.get_all_clients(current_user)

@router.get("/{client_id}")
async def get_single_client(client_id: str, current_user: dict = Depends(get_approved_user)):
    """Get a specific client."""
    client = await client_service.get_client(client_id, current_user)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}")
async def update_existing_client(client_id: str, client_update: ClientUpdate, current_user: dict = Depends(get_approved_user)):
    """Update a client."""
    updated = await client_service.update_client(client_id, current_user, client_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")
    return updated

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_client(client_id: str, current_user: dict = Depends(get_approved_user)):
    """Delete a client."""
    success = await client_service.delete_client(client_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    return None
