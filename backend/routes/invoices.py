"""
Invoice Routes — Full CRUD + search + status management.
All endpoints are protected with JWT authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from auth import get_current_user, get_approved_user
from models.invoice import InvoiceCreate, InvoiceUpdate, InvoiceStatusUpdate
from services import invoice_service

router = APIRouter()

@router.get("/stats/dashboard")
async def get_stats(current_user: dict = Depends(get_approved_user)):
    """Returns stats (Blocked for pending)."""
    return await invoice_service.get_dashboard_stats(current_user)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_invoice(invoice: InvoiceCreate, current_user: dict = Depends(get_approved_user)):
    """Create a new invoice (Blocked for pending)."""
    return await invoice_service.create_invoice(invoice, current_user)

@router.get("/")
async def list_all_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    location: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_approved_user)
):
    """List all invoices (Blocked for pending)."""
    return await invoice_service.get_all_invoices(current_user, skip=skip, limit=limit, search=search, location=location, user_id=user_id)

@router.get("/{invoice_id}")
async def get_single_invoice(invoice_id: str, current_user: dict = Depends(get_approved_user)):
    """Get a specific invoice (Blocked for pending)."""
    invoice = await invoice_service.get_invoice(invoice_id, current_user)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found or access denied")
    return invoice

@router.put("/{invoice_id}")
async def update_existing_invoice(invoice_id: str, invoice_update: InvoiceUpdate, current_user: dict = Depends(get_approved_user)):
    """Update an invoice (Blocked for pending)."""
    updated = await invoice_service.update_invoice(invoice_id, current_user, invoice_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Invoice not found or access denied")
    return updated

@router.patch("/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, status_update: InvoiceStatusUpdate, current_user: dict = Depends(get_approved_user)):
    """Update status (Blocked for pending)."""
    updated = await invoice_service.update_invoice(invoice_id, current_user, status_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Invoice not found or access denied")
    return updated

@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_invoice(invoice_id: str, current_user: dict = Depends(get_approved_user)):
    """Delete an invoice (Blocked for pending)."""
    success = await invoice_service.delete_invoice(invoice_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice not found or access denied")
    return None
