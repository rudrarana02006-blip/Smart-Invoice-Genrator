from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import google.generativeai as genai
import json
import re
from datetime import datetime, timezone
from auth import get_approved_user
from database import get_db
from config import settings

from config import settings, get_gemini_model

router = APIRouter()

# Configure Gemini with Dynamic Discovery for Vision
genai.configure(api_key=settings.GEMINI_API_KEY)
vision_model = get_gemini_model(vision=True)

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
    role_str = str(current_user.get("role", "")).lower()
    is_admin = role_str == "admin"
    org_id = current_user.get("org_id")
    
    print(f"[DEBUG] Design upload attempt by: {current_user.get('email')} | Role: {role_str} | OrgID: {org_id}")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID missing from profile.")
        
    is_independent = str(org_id) == str(current_user.get("_id", ""))
    
    if not (is_admin or is_independent):
        print(f"[DEBUG] Permission Denied: is_admin={is_admin}, is_independent={is_independent}")
        raise HTTPException(status_code=403, detail="Only Admins or Independent users can set custom formats.")

    try:
        content = await file.read()
        
        # 1. AI Vision Prompt for High-Fidelity Cloning
        prompt = (
            "You are a Senior UI/UX Architect specializing in pixel-perfect invoice replication. "
            "Analyze the attached invoice sample. Your mission is to CLONE its structure exactly. "
            "\n\nCRITICAL ARCHITECTURAL DECISION:"
            "\n- If the sample is a formal, traditional tax invoice with a centered header, tabular grid lines throughout, and NO modern boxes or glass elements, SET 'layout': 'classic'."
            "\n- Otherwise, for modern or industrial designs, SET 'layout': 'modern'."
            "\n\nEXTRACT THESE TOKENS:"
            "\n1. 'primary_color': Brand hex code."
            "\n2. 'font_family': EXACT font or family (e.g. 'Times New Roman', 'Inter')."
            "\n3. 'layout': 'modern' or 'classic'."
            "\n4. 'hide_borders': Boolean."
            "\n5. 'css_override': NUCLEAR OVERRIDE. Use this to destroy our default aesthetic if it doesn't match."
            "\n   - HIDE EVERYTHING NOT IN SAMPLE: .dot-ind, .top-strip, .bottom-strip, .glass-panel { display: none !important; }"
            "\n   - ALIGNMENT: If header is centered, use .header { justify-content: center !important; text-align: center; }"
            "\n   - GRIDS: If sample has heavy black grid lines, use: table.items td, table.items th { border: 1pt solid #000 !important; }"
            "\n   - TYPOGRAPHY: Force font-weight and letter-spacing to match."
            "\n\nOutput ONLY a valid JSON object. DO NOT BE POLITE. BE AGGRESSIVE. CLONE IT."
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
        design_coll = get_db()['design_systems']
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
            
        design_coll = get_db()['design_systems']
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
    design_coll = get_db()['design_systems']
    await design_coll.delete_one({"org_id": org_id})
    return {"message": "Reset to default format successfully."}
