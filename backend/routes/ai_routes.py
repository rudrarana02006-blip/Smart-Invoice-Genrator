"""
AI routes — Gemini API integration for professional description expansion.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from google.api_core import exceptions

from auth import get_current_user, get_approved_user
from config import settings

router = APIRouter()

# Configure Gemini
if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
    print("CRITICAL: GEMINI_API_KEY IS MISSING IN .ENV FILE")
    genai.configure(api_key="MISSING")
else:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Diagnostic: List available models to terminal
try:
    print("--- AI DIAGNOSTIC: VERIFYING MODELS ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f'Available Model: {m.name}')
except Exception as e:
    print(f'Model list failed: {e}')

# Standardize Model Name (Using flash-latest for maximum compatibility)
model = genai.GenerativeModel(model_name='gemini-flash-latest')

class DescriptionRequest(BaseModel):
    phrase: str

class NoteRequest(BaseModel):
    client_name: str
    total_amount: float
    currency: str = "INR"

class TaxRequest(BaseModel):
    address: str
    items: list[str] = []

import os
# Verify API Key Loading
if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
    print("CRITICAL: GEMINI_API_KEY is missing or default!")
else:
    print(f"DEBUG: Using API Key: {settings.GEMINI_API_KEY[:5]}...")

@router.get("/check-key")
async def check_key():
    """Diagnostic endpoint to check key status."""
    if not settings.GEMINI_API_KEY:
        return {"status": "error", "message": "API KEY MISSING"}
    return {"status": "ok", "prefix": settings.GEMINI_API_KEY[:5]}

import re

def clean_ai_response(text: str) -> str:
    """Removes Markdown and extra formatting from Gemini responses."""
    if not text: return ""
    # Remove introductory sentences like "Here is a description:"
    text = re.sub(r'^(Here is|Sure|Based on|I have expanded).*?:', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'[*_]{1,3}', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = text.replace('`', '')
    # If the AI provided multiple options, take the first one
    if "\n" in text:
        text = text.split("\n")[0]
    return text.strip().strip('"').strip("'")

@router.post("/expand-description")
async def expand_description(
    request: DescriptionRequest,
    current_user: dict = Depends(get_approved_user)
):
    try:
        # Strictly instructed to be factual and avoid hallucination
        prompt = (
            f"Act as a professional corporate consultant. Refine and expand the following phrase "
            f"into a formal, meticulously detailed invoice line-item description: '{request.phrase}'. "
            f"STRICT RULES: Use sophisticated, high-end terminology. Make it sound premium and professional. "
            f"Do NOT add quantities (like 'one' or '1') or speculative prices. "
            f"Just make the description more descriptive and enterprise-grade. "
            f"Output ONLY the refined description text."
        )
        response = model.generate_content(prompt)
        cleaned = clean_ai_response(response.text)
        return {"expanded_description": cleaned, "suggestion": cleaned}
    except exceptions.ResourceExhausted:
        raise HTTPException(status_code=429, detail="Quota reached. Please try again in 30 seconds.")
    except exceptions.NotFound:
        raise HTTPException(status_code=404, detail="AI Model Configuration Mismatch. Check terminal logs.")
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            raise HTTPException(status_code=404, detail="AI Model Configuration Mismatch. Check terminal logs.")
        if "429" in error_str or "quota" in error_str.lower():
            raise HTTPException(status_code=429, detail="Quota reached. Please try again in 30 seconds.")
        raise HTTPException(status_code=500, detail=error_str)

@router.post("/draft-note")
async def draft_note(
    request: NoteRequest,
    current_user: dict = Depends(get_approved_user)
):
    """
    Drafts a professional thank-you note and payment terms.
    """
    try:
        symbol = "₹" if request.currency == "INR" else "$"
        prompt = (
            f"Draft concise invoice thank-you and 15-day terms for {request.client_name}. "
            f"The total is {symbol}{request.total_amount}. "
            f"The currency is {request.currency}. Use the symbol {symbol} for all amounts. "
            f"Max 40 words."
        )
        response = model.generate_content(prompt)
        cleaned = clean_ai_response(response.text)
        return {"note": cleaned, "suggestion": cleaned}
    except exceptions.ResourceExhausted:
        raise HTTPException(status_code=429, detail="Quota reached. Please try again in 30 seconds.")
    except exceptions.NotFound:
        raise HTTPException(status_code=404, detail="AI Model Configuration Mismatch. Check terminal logs.")
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            raise HTTPException(status_code=404, detail="AI Model Configuration Mismatch. Check terminal logs.")
        if "429" in error_str or "quota" in error_str.lower():
            raise HTTPException(status_code=429, detail="Quota reached. Please try again in 30 seconds.")
        raise HTTPException(status_code=500, detail=error_str)

@router.post("/suggest-tax")
async def suggest_tax(
    request: TaxRequest,
    current_user: dict = Depends(get_approved_user)
):
    """
    Suggests tax rates based on the client's address.
    """
    try:
        items_str = ", ".join(request.items) if request.items else "General Services"
        prompt = (
            f"Analyze this client address: '{request.address}' and these invoice items: '{items_str}'.\n"
            f"1. Detect the country and region.\n"
            f"2. If India: Determine if Interstate (IGST) or Intrastate (CGST+SGST) and the correct GST slab (5, 12, 18, 28%).\n"
            f"3. If USA: Suggest the state sales tax rate (e.g., 6.25% for MA, 8.875% for NY).\n"
            f"4. If Europe/UK: Suggest the standard VAT rate (e.g., 20% for UK, 19% for Germany).\n"
            f"5. If Other: Suggest a standard regional tax rate.\n\n"
            f"Output ONLY a JSON object with these keys:\n"
            f"- 'tax_1_name': String (e.g., 'CGST', 'Sales Tax', 'VAT')\n"
            f"- 'tax_1_rate': Float (percentage)\n"
            f"- 'tax_2_name': String (e.g., 'SGST', 'IGST') or empty string\n"
            f"- 'tax_2_rate': Float (percentage, 0 if not applicable)\n"
            f"- 'duty_name': String (e.g., 'Import Duty', 'Export Duty') or empty string\n"
            f"- 'duty_rate': Float (percentage, 0 if not applicable)\n\n"
            f"Example for International Export: {{\"tax_1_name\": \"VAT (Zero Rated)\", \"tax_1_rate\": 0, \"tax_2_name\": \"\", \"tax_2_rate\": 0, \"duty_name\": \"Export Duty\", \"duty_rate\": 2.5}}"
        )
        response = model.generate_content(prompt)
        
        # Extract JSON using regex
        import json
        match = re.search(r"\{.*\}", response.text.replace("\n", ""), re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {
                "tax_1_name": data.get("tax_1_name", "Tax"),
                "tax_1_rate": float(data.get("tax_1_rate", 0)),
                "tax_2_name": data.get("tax_2_name", ""),
                "tax_2_rate": float(data.get("tax_2_rate", 0)),
                "duty_name": data.get("duty_name", ""),
                "duty_rate": float(data.get("duty_rate", 0))
            }
        
        return {
            "tax_1_name": "Tax", "tax_1_rate": 0.0, 
            "tax_2_name": "", "tax_2_rate": 0.0,
            "duty_name": "", "duty_rate": 0.0
        }
    except exceptions.ResourceExhausted:
        raise HTTPException(status_code=429, detail="Quota reached. Please try again in 30 seconds.")
    except exceptions.NotFound:
        raise HTTPException(status_code=404, detail="AI Model Configuration Mismatch. Check terminal logs.")
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            raise HTTPException(status_code=404, detail="AI Model Configuration Mismatch. Check terminal logs.")
        if "429" in error_str or "quota" in error_str.lower():
            raise HTTPException(status_code=429, detail="Quota reached. Please try again in 30 seconds.")
        raise HTTPException(status_code=500, detail=error_str)
