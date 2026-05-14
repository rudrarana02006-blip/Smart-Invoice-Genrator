"""
PDF Service — Generates professional A4 invoice PDFs using WeasyPrint + Jinja2.
Company identity is injected from config/settings so it matches the .env values.
"""
import os
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

# Import settings lazily to avoid circular imports at module level
def _get_settings():
    from config import settings
    return settings


from database import get_profile_collection, db

async def generate_invoice_pdf(invoice_data: dict, org_id: str) -> bytes:
    """
    Render the invoice_pdf.html Jinja2 template and produce a PDF via WeasyPrint.
    Falls back with a clear message if WeasyPrint system deps are missing.
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint is not available. Install system dependencies: "
            "brew install pango cairo libffi (macOS) or "
            "apt-get install libpango-1.0-0 libcairo2 (Linux)."
        )

    settings = _get_settings()
    
    # Fetch Organization Admin Profile from DB
    # In our architecture, the org_id IS the Admin's user ID.
    profiles = get_profile_collection()
    user_profile = await profiles.find_one({"user_id": org_id})

    # Build the company context dict
    if user_profile:
        # If we have a profile, use it. Fallback to empty string for missing fields.
        company = {
            "name":         user_profile.get("company_name", ""),
            "tagline":      user_profile.get("company_tagline", ""),
            "email":        user_profile.get("email", ""),
            "phone":        user_profile.get("phone", ""),
            "address":      user_profile.get("address", ""),
            "gstin":        user_profile.get("gstin", ""),
            "pan":          user_profile.get("pan", ""),
            "website":      user_profile.get("website", ""),
            "bank_name":    user_profile.get("bank_name", ""),
            "bank_account": user_profile.get("bank_account", ""),
            "bank_ifsc":    user_profile.get("bank_ifsc", ""),
            "bank_account_name": user_profile.get("company_name", ""),
        }
        
        # Handle the case where bank details might be in the bank_accounts list
        accounts = user_profile.get("bank_accounts", [])
        if accounts and not company["bank_name"]:
            primary = accounts[0]
            company["bank_name"] = primary.get("bank_name", "")
            company["bank_account"] = primary.get("account_no", "")
            company["bank_ifsc"] = primary.get("ifsc", "")
            company["bank_account_name"] = primary.get("account_name", "")
    else:
        # No profile found, use empty strings (forcing the user to enter data in the UI)
        company = {
            "name":         "Company Name Required",
            "tagline":      "",
            "email":        "",
            "phone":        "",
            "address":      "",
            "gstin":        "",
            "pan":          "",
            "website":      "",
            "bank_name":    "",
            "bank_account": "",
            "bank_ifsc":    "",
            "bank_account_name": "",
        }

    # Override bank details if the invoice has a selected bank
    selected_bank = invoice_data.get("selected_bank")
    if selected_bank:
        company["bank_name"] = selected_bank.get("bank_name", company["bank_name"])
        company["bank_account"] = selected_bank.get("account_no", company["bank_account"])
        company["bank_ifsc"] = selected_bank.get("ifsc", company["bank_ifsc"])
        company["bank_account_name"] = selected_bank.get("account_name", company["name"])

    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates"
    )
    
    # Null Safety: Convert all None values to empty strings to prevent crashes
    for k, v in company.items():
        if v is None:
            company[k] = ""
            
    for k, v in invoice_data.items():
        if v is None:
            invoice_data[k] = ""

    # Fetch Custom Design Tokens (AI extracted)
    design_coll = db['design_systems']
    design_doc = await design_coll.find_one({"org_id": org_id})
    style_tokens = design_doc.get("tokens", {}) if design_doc else {}

    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("invoice_pdf.html")

    try:
        rendered_html = template.render(
            invoice=invoice_data, 
            company=company,
            style=style_tokens
        )
        return HTML(string=rendered_html, base_url=templates_dir).write_pdf()
    except Exception as e:
        import traceback
        print("FULL TRACEBACK FOR PDF ERROR:")
        traceback.print_exc()
        raise e
