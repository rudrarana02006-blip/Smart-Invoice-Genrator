"""
Invoice Service — Business logic for invoice CRUD operations.
Handles auto-calculation of subtotals, CGST, SGST, and totals.
"""

from datetime import datetime, timezone
from bson import ObjectId

from database import get_invoice_collection
from models.invoice import InvoiceCreate, InvoiceUpdate, InvoiceStatus, InvoiceInDB


def calculate_invoice_totals(invoice_data: dict) -> dict:
    """
    Calculates line item amounts, subtotal, taxes, and grand total.
    Mutates the invoice_data dict in place.
    """
    subtotal = 0.0
    
    # Calculate each line item's amount
    for item in invoice_data.get('items', []):
        amount = item['quantity'] * item['rate']
        item['amount'] = round(amount, 2)
        subtotal += amount
        
    subtotal = round(subtotal, 2)
    invoice_data['subtotal'] = subtotal
    
    # Calculate taxes based on subtotal
    cgst_rate = invoice_data.get('cgst_rate', 0)
    sgst_rate = invoice_data.get('sgst_rate', 0)
    
    cgst_amount = round(subtotal * (cgst_rate / 100), 2)
    sgst_amount = round(subtotal * (sgst_rate / 100), 2)
    
    total_tax = round(cgst_amount + sgst_amount, 2)
    
    invoice_data['cgst_amount'] = cgst_amount
    invoice_data['sgst_amount'] = sgst_amount
    invoice_data['total_tax'] = total_tax
    invoice_data['grand_total'] = round(subtotal + total_tax, 2)
    
    return invoice_data


import re

from services.numbering_service import format_invoice_number

async def create_invoice(invoice: InvoiceCreate, current_user: dict) -> dict:
    invoices = get_invoice_collection()
    invoice_dict = invoice.model_dump()
    invoice_dict = calculate_invoice_totals(invoice_dict)
    
    org_id = current_user.get("org_id")
    user_email = current_user.get("email")
    
    # Check status
    from models.user import UserStatus
    if current_user.get("status") == UserStatus.PENDING:
        raise HTTPException(status_code=403, detail="Your account is pending approval.")
    
    # Use provided invoice number or generate ATOMIC one
    if not invoice_dict.get("invoice_number"):
        # Default prefix logic
        prefix = invoice_dict.get("invoice_number_prefix", "INV-")
        if not prefix.endswith("-"):
            prefix += "-"
        invoice_dict["invoice_number"] = await format_invoice_number(org_id, prefix)
    
    invoice_dict["org_id"] = org_id
    invoice_dict["created_by"] = user_email
    invoice_dict["status"] = InvoiceStatus.DRAFT.value
    invoice_dict["created_at"] = datetime.now(timezone.utc)
    invoice_dict["updated_at"] = invoice_dict["created_at"]
    
    result = await invoices.insert_one(invoice_dict)
    invoice_dict["_id"] = str(result.inserted_id)
    return invoice_dict

async def get_all_invoices(current_user: dict, skip: int = 0, limit: int = 50, search: str = None, location: str = None, user_id: str = None) -> list:
    invoices = get_invoice_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    if current_user.get("role") == UserRole.ADMIN:
        # Admin sees everything in the org
        query = {"org_id": org_id}
        if user_id:
            from database import get_user_collection
            users_coll = get_user_collection()
            try:
                target_user = await users_coll.find_one({"_id": ObjectId(user_id), "org_id": org_id})
                if target_user:
                    query["created_by"] = target_user["email"]
            except:
                pass # Fallback to org-wide if ID is invalid
    else:
        # User sees only their own
        query = {"org_id": org_id, "created_by": current_user["email"]}
    
    if search:
        query["$or"] = [
            {"client_name": {"$regex": search, "$options": "i"}},
            {"invoice_number": {"$regex": search, "$options": "i"}}
        ]
    
    if location:
        # Search for the city name within the client_address string
        query["client_address"] = {"$regex": location, "$options": "i"}
        
    cursor = invoices.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return [{**doc, "_id": str(doc["_id"])} async for doc in cursor]

async def get_invoice(invoice_id: str, current_user: dict) -> dict:
    invoices = get_invoice_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    query = {"_id": ObjectId(invoice_id), "org_id": org_id}
    if current_user.get("role") != UserRole.ADMIN:
        query["created_by"] = current_user["email"]
        
    invoice = await invoices.find_one(query)
    if invoice:
        invoice["_id"] = str(invoice["_id"])
    return invoice

async def update_invoice(invoice_id: str, current_user: dict, update_data: InvoiceUpdate) -> dict:
    invoices = get_invoice_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    query = {"_id": ObjectId(invoice_id), "org_id": org_id}
    if current_user.get("role") != UserRole.ADMIN:
        query["created_by"] = current_user["email"]
        
    existing = await invoices.find_one(query)
    if not existing:
        return None
        
    update_dict = update_data.model_dump(exclude_unset=True)
    merged_data = {**existing, **update_dict}
    
    if 'items' in update_dict or 'cgst_rate' in update_dict or 'sgst_rate' in update_dict:
        merged_data = calculate_invoice_totals(merged_data)
        update_dict.update({
            'subtotal': merged_data['subtotal'],
            'cgst_amount': merged_data['cgst_amount'],
            'sgst_amount': merged_data['sgst_amount'],
            'total_tax': merged_data['total_tax'],
            'grand_total': merged_data['grand_total']
        })
        if 'items' in update_dict:
             update_dict['items'] = merged_data['items']
             
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    await invoices.update_one(query, {"$set": update_dict})
    return await get_invoice(invoice_id, current_user)

async def delete_invoice(invoice_id: str, current_user: dict) -> bool:
    invoices = get_invoice_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    query = {"_id": ObjectId(invoice_id), "org_id": org_id}
    if current_user.get("role") != UserRole.ADMIN:
        query["created_by"] = current_user["email"]
        
    result = await invoices.delete_one(query)
    return result.deleted_count > 0

async def get_dashboard_stats(current_user: dict) -> dict:
    invoices = get_invoice_collection()
    org_id = current_user.get("org_id")
    
    from models.user import UserRole
    if current_user.get("role") == UserRole.ADMIN:
        match_query = {"org_id": org_id}
    else:
        match_query = {"org_id": org_id, "created_by": current_user["email"]}
        
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "total_invoices": {"$sum": 1},
                "total_revenue": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "paid"]}, "$grand_total", 0]
                    }
                },
                "pending_amount": {
                    "$sum": {
                        "$cond": [{"$in": ["$status", ["sent", "overdue"]]}, "$grand_total", 0]
                    }
                }
            }
        }
    ]
    result = await invoices.aggregate(pipeline).to_list(1)
    if result:
        stats = result[0]
        stats.pop('_id', None)
        return stats
    return {"total_invoices": 0, "total_revenue": 0, "pending_amount": 0}
