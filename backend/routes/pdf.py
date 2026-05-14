"""
PDF routes — Invoice PDF export.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from auth import get_current_user
from services import invoice_service
from services.pdf_service import generate_invoice_pdf

router = APIRouter()

@router.get("/{invoice_id}")
async def download_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Generate and download a PDF version of the invoice."""
    # 1. Fetch invoice with ownership check
    invoice = await invoice_service.get_invoice(invoice_id, current_user)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found or access denied")
        
    # 2. Generate PDF
    try:
        # Pass the org_id so the PDF pulls the organization's Admin profile
        pdf_bytes = await generate_invoice_pdf(invoice, current_user.get("org_id"))
        
        # 3. Return as a file download
        filename = f"{invoice['invoice_number']}.pdf"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
