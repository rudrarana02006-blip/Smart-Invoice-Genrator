"""
Email routes — AI-powered invoice dispatching with Admin CC.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime, timezone
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import google.generativeai as genai

from auth import get_approved_user
from services import invoice_service
from services.pdf_service import generate_invoice_pdf
from config import settings
from database import get_invoice_collection
from bson import ObjectId

router = APIRouter()

# Configure Gemini (shared logic with ai_routes)
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name='gemini-flash-latest')
else:
    model = None

def get_email_tone(client_name: str) -> str:
    """Detects tone based on client name formatting."""
    formal_indicators = ["Mr.", "Ms.", "Mrs.", "Dr.", "Prof.", "Inc", "Ltd", "Corp"]
    if any(ind in client_name for ind in formal_indicators):
        return "Formal"
    # If it's a single name or a first name, use friendly
    parts = client_name.strip().split()
    if len(parts) == 1:
        return "Friendly"
    return "Professional"

async def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    pdf_bytes: bytes,
    filename: str,
    cc_email: str = None
):
    """Sends an email with a PDF attachment using SMTP."""
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print("CRITICAL: SMTP credentials missing in .env (MAIL_USERNAME/MAIL_PASSWORD).")
        return False

    msg = MIMEMultipart()
    msg['From'] = settings.MAIL_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    if cc_email:
        msg['Cc'] = cc_email

    msg.attach(MIMEText(body, 'plain'))

    part = MIMEApplication(pdf_bytes, Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)

    recipients = [to_email]
    if cc_email:
        recipients.append(cc_email)

    try:
        # Use Port 587 for TLS (Standard) or 465 for SSL (Restricted Networks)
        print(f"DEBUG: Attempting SMTP connection to {settings.MAIL_SERVER}:{settings.MAIL_PORT}...")
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10)
        server.set_debuglevel(1) # Enable to see raw SMTP traffic in logs
        server.starttls()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_USERNAME, recipients, msg.as_string())
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError:
        print("SMTP ERROR: Authentication Failed. Verify your Google App Password (16 characters).")
    except smtplib.SMTPConnectError:
        print(f"SMTP ERROR: Connection Refused. Check port {settings.MAIL_PORT} or firewall.")
    except Exception as e:
        print(f"SMTP GENERAL ERROR: {type(e).__name__} - {e}")
    return False

@router.post("/send-invoice-email/{invoice_id}")
async def send_invoice_email(
    invoice_id: str,
    current_user: dict = Depends(get_approved_user)
):
    """
    Drafts an AI email, attaches the invoice PDF, and sends it to the client with CC to Admin.
    """
    # 1. Fetch Invoice & Profile
    invoice = await invoice_service.get_invoice(invoice_id, current_user)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    client_email = invoice.get("client_email")
    if not client_email:
        raise HTTPException(status_code=400, detail="Client email is missing in invoice data")

    from database import get_profile_collection
    profiles = get_profile_collection()
    profile = await profiles.find_one({"user_id": current_user.get("org_id")})
    company_name = (profile or {}).get("company_name", "Our Company")

    # 2. AI Email Drafting
    tone = get_email_tone(invoice.get("client_name", ""))
    body = f"Hello {invoice['client_name']},\n\nPlease find the attached invoice {invoice['invoice_number']} for the amount of {invoice.get('currency', 'INR')} {invoice['grand_total']}.\n\nRegards,\n{company_name}"
    
    if model:
        try:
            prompt = (
                f"Write a personalized email body to {invoice['client_name']} for invoice {invoice['invoice_number']} "
                f"(Total: {invoice['grand_total']}). Mention the invoice is attached. Tone: {tone}. "
                f"Specifically mention: 'On behalf of {company_name}, we are pleased to share your latest invoice.' "
                f"Keep it under 60 words. No subject line, just body."
            )
            response = model.generate_content(prompt)
            if response and response.text:
                body = response.text.strip()
        except Exception as ai_err:
            print(f"AI Drafting fallback: {ai_err}")

    # 3. Generate PDF
    try:
        pdf_bytes = await generate_invoice_pdf(invoice, current_user.get("org_id"))
    except Exception as pdf_err:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(pdf_err)}")

    # 4. Send Email
    subject = f"Invoice {invoice['invoice_number']} from {company_name}"
    filename = f"Invoice_{invoice['invoice_number']}.pdf"
    
    # CC to the Admin of the organization
    from database import get_user_collection
    users_coll = get_user_collection()
    org_id = current_user.get("org_id")
    
    # Fetch the Admin user to get their actual email
    admin_user = await users_coll.find_one({"_id": ObjectId(org_id), "role": "admin"})
    if not admin_user:
        # Fallback to org_id if it's already an email (legacy) or current user if admin
        admin_user = await users_coll.find_one({"email": org_id, "role": "admin"})
    
    cc_admin = admin_user["email"] if admin_user else current_user["email"]
    
    success = await send_email_with_attachment(
        to_email=client_email,
        subject=subject,
        body=body,
        pdf_bytes=pdf_bytes,
        filename=filename,
        cc_email=cc_admin
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email. Check SMTP settings.")

    # 5. Update Status
    invoices = get_invoice_collection()
    await invoices.update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": {
            "status": "sent",
            "last_sent": datetime.now(timezone.utc)
        }}
    )

    return {
        "message": "Invoice dispatched successfully!",
        "cc_admin": cc_admin,
        "recipient": client_email
    }
