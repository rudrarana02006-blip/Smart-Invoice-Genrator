"""
Profile routes — Company Profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone

from auth import get_current_user, get_approved_user
from database import get_profile_collection
from models.profile import CompanyProfile

router = APIRouter()

@router.get("/")
async def get_profile(current_user: dict = Depends(get_approved_user)):
    """Retrieve the organization's company profile (synced for all users)."""
    profiles = get_profile_collection()
    # All users in the org pull from the org_id (which is the Admin's user ID)
    profile = await profiles.find_one({"user_id": current_user["org_id"]})
    
    if not profile:
        # Fallback to defaults
        return {
            "company_name": "",
            "address": "",
            "gstin": "",
            "pan": "",
            "phone": "",
            "email": current_user["email"],
            "bank_name": "",
            "bank_account": "",
            "bank_ifsc": ""
        }
    
    profile["_id"] = str(profile["_id"])
    return profile

@router.put("/")
async def update_profile(profile_data: CompanyProfile, current_user: dict = Depends(get_approved_user)):
    """Update the organization's company profile. Restricted to Admins."""
    from models.user import UserRole
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admins can update the company profile.")
        
    profiles = get_profile_collection()
    update_dict = profile_data.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    await profiles.update_one(
        {"user_id": current_user["_id"]}, # For Admins, org_id == _id
        {
            "$set": update_dict,
            "$setOnInsert": {
                "user_id": current_user["_id"],
                "created_at": update_dict["updated_at"]
            }
        },
        upsert=True
    )
    
    return {"status": "success", "message": "Organization profile updated successfully"}
