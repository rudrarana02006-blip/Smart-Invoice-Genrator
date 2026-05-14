"""
Organization Management routes — Admin only.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from auth import get_current_user, get_admin_user
from database import get_user_collection
from models.user import UserRole, UserStatus

router = APIRouter()

@router.get("/users")
async def list_org_users(current_user: dict = Depends(get_admin_user)):
    """List all users in the organization."""
    users = get_user_collection()
    org_id = current_user["org_id"]
    
    cursor = users.find({"org_id": org_id})
    result = []
    async for user in cursor:
        result.append({
            "id": str(user["_id"]),
            "email": user["email"],
            "role": user.get("role", "user"),
            "status": user.get("status", "approved"),
            "created_at": user.get("created_at")
        })
    return result

@router.post("/approve-user")
async def approve_user(user_email: str, current_user: dict = Depends(get_admin_user)):
    """Approve a pending user in the organization."""
    users = get_user_collection()
    org_id = current_user["org_id"]
    
    # Verify user belongs to this org and is pending
    target = await users.find_one({"email": user_email, "org_id": org_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found in your organization")
        
    await users.update_one(
        {"email": user_email},
        {"$set": {"status": UserStatus.APPROVED}}
    )
    
    return {"message": f"User {user_email} has been approved."}

@router.post("/reject-user")
async def reject_user(user_email: str, current_user: dict = Depends(get_current_user)):
    """Reject and remove a pending user."""
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    users = get_user_collection()
    org_id = current_user["org_id"]
    
    await users.delete_one({"email": user_email, "org_id": org_id, "status": UserStatus.PENDING})
    return {"message": f"User {user_email} has been rejected."}

@router.post("/toggle-status/{user_id}")
async def toggle_user_status(user_id: str, current_user: dict = Depends(get_admin_user)):
    """Toggle user status between APPROVED and PENDING."""
        
    from bson import ObjectId
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    users = get_user_collection()
    org_id = current_user["org_id"]
    
    # Cannot toggle yourself
    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot toggle your own status")
        
    target = await users.find_one({"_id": obj_id, "org_id": org_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found in your organization")
        
    # Safety Check: Cannot toggle an Admin
    if target.get("role") == UserRole.ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Admin status cannot be modified. Protects the organization owner."
        )
        
    current_status = target.get("status", UserStatus.APPROVED)
    new_status = UserStatus.PENDING if current_status == UserStatus.APPROVED else UserStatus.APPROVED
    
    await users.update_one(
        {"_id": obj_id},
        {"$set": {"status": new_status, "token_version": target.get("token_version", 0) + 1}}
    )
    
    return {
        "message": f"User status updated to {new_status}",
        "new_status": new_status
    }

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: dict = Depends(get_admin_user)):
    """Permanently delete a user from the organization. Admin only."""
    from bson import ObjectId
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    users = get_user_collection()
    org_id = current_user["org_id"]
    
    # Cannot delete yourself through this route
    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account here. Use Settings -> Delete Account.")
        
    # Verify user belongs to this org
    target = await users.find_one({"_id": obj_id, "org_id": org_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found in your organization")
        
    # Note: We only delete the user record. Invoices created by them are kept for accounting.
    await users.delete_one({"_id": obj_id})
    
    return None
