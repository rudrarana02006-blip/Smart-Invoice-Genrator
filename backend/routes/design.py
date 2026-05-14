from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import google.generativeai as genai
import json
import re
from datetime import datetime, timezone
from auth import get_approved_user
from database import db
from config import settings

router = APIRouter()

# Configure Gemini 2.0 Flash for High-Speed Vision
genai.configure(api_key=settings.GEMINI_API_KEY)
vision_model = genai.GenerativeModel(model_name='models/gemini-2.0-flash')

@router.post("/analyze")
async def analyze_sample_format(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_approved_user)
):
    """
    Analyzes an uploaded invoice image/PDF and extracts design tokens.
    Only available to Independent users or Admins.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Session expired.")
        
    # Permission Check
    is_admin = current_user.get("role") == "admin"
    org_id = current_user.get("org_id")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID missing from profile.")
        
    is_independent = org_id == str(current_user.get("_id", ""))
    
    if not (is_admin or is_independent):
        raise HTTPException(status_code=403, detail="Only Admins or Independent users can set custom formats.")

    try:
        content = await file.read()
        
        # 1. AI Vision Prompt for Pixel-Perfect Cloning
        prompt = (
            "Analyze this invoice sample image with extreme precision. Your goal is to CLONE its visual identity. "
            "Extract the following tokens as a JSON object: "
            "1. 'primary_color': Hex code of the main brand color. "
            "2. 'font_family': Name of the closest web-safe font or Google Font. "
            "3. 'header_style': ['left', 'center', 'split']. "
            "4. 'css_override': A string containing custom CSS rules to make our template match this sample. "
            "   Focus on: .brand-name font-size, .top-strip height, .party-block border styles, and .items thead background. "
            "   IMPORTANT: Use high-precision CSS selectors to override the default styles. "
            "5. 'accent_bg': A very light version of the primary color for backgrounds. "
            "6. 'border_radius': The exact roundness of boxes (e.g. '4px', '12px'). "
            "\nOutput ONLY the JSON object."
        )
        
        response = vision_model.generate_content([
            prompt,
            {"mime_type": file.content_type, "data": content}
        ])
        
        # 2. Extract and Validate JSON
        match = re.search(r"\{.*\}", response.text.replace("\n", ""), re.DOTALL)
        if not match:
            raise HTTPException(status_code=500, detail="AI failed to extract design tokens from the image.")
            
        design_tokens = json.loads(match.group())
        
        # 3. Store in Database
        design_coll = db['design_systems']
        await design_coll.update_one(
            {"org_id": org_id},
            {"$set": {
                "tokens": design_tokens,
                "sample_mime": file.content_type,
                "updated_at": datetime.now(timezone.utc),
                "created_by": current_user["email"]
            }},
            upsert=True
        )
        
        return {
            "status": "success",
            "message": "Invoice style cloned successfully!",
            "tokens": design_tokens
        }
        
    except Exception as e:
        print(f"❌ DESIGN ANALYSIS ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_design(current_user: dict = Depends(get_approved_user)):
    """Fetches the active design system for the current organization with fail-proof logic."""
    try:
        if not current_user:
            return {"status": "default", "tokens": None}
            
        org_id = current_user.get("org_id")
        if not org_id:
            return {"status": "default", "tokens": None}
            
        design_coll = db['design_systems']
        design = await design_coll.find_one({"org_id": org_id})
        
        if not design or "tokens" not in design:
            return {"status": "default", "tokens": None}
            
        return {"status": "custom", "tokens": design["tokens"]}
        
    except Exception as e:
        print(f"⚠️ DESIGN RETRIEVAL WARNING: {str(e)}")
        return {"status": "default", "tokens": None}

@router.delete("/reset")
async def reset_to_default(current_user: dict = Depends(get_approved_user)):
    """Resets the organization to the default invoice format."""
    org_id = current_user.get("org_id")
    design_coll = db['design_systems']
    await design_coll.delete_one({"org_id": org_id})
    return {"message": "Reset to default format successfully."}
