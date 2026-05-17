"""
Invoice Pydantic models — request/response schemas.
Handles validation for invoices and line items.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from models.profile import BankAccount

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PENDING = "pending"
    OVERDUE = "overdue"
    TEMPLATE = "template"


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    AED = "AED"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    SGD = "SGD"

class RecurrenceInterval(str, Enum):
    NONE = "none"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class LineItem(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: str = Field(default="Units")
    rate: float = Field(..., ge=0)
    amount: float = Field(default=0, ge=0)  # Calculated field (quantity * rate)


class InvoiceBase(BaseModel):
    client_name: str
    client_email: str
    client_address: Optional[str] = None
    
    date: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime
    currency: Currency = Currency.INR
    
    # Tax configuration (Percentages)
    cgst_rate: float = Field(default=0, ge=0, description="CGST percentage")
    sgst_rate: float = Field(default=0, ge=0, description="SGST percentage")
    
    notes: Optional[str] = None
    
    # Selected Bank Details
    selected_bank: Optional[BankAccount] = None

    # Tracking Flags
    is_sent: bool = Field(default=False)
    is_paid: bool = Field(default=False)
    
    # Recurring/Template Support
    is_template: bool = Field(default=False)
    recurrence: RecurrenceInterval = RecurrenceInterval.NONE


class InvoiceCreate(InvoiceBase):
    items: List[LineItem]
    invoice_number: Optional[str] = None


class InvoiceUpdate(InvoiceBase):
    items: Optional[List[LineItem]] = None
    status: Optional[InvoiceStatus] = None
    is_sent: Optional[bool] = None
    is_paid: Optional[bool] = None


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


class InvoiceInDB(InvoiceCreate):
    id: str = Field(alias="_id")
    invoice_number: str
    status: InvoiceStatus = InvoiceStatus.DRAFT
    subtotal: float
    
    # Dynamic Taxes
    tax_1_name: str = "CGST"
    tax_1_rate: float = 9.0
    tax_1_amount: float = 0.0
    
    tax_2_name: Optional[str] = "SGST"
    tax_2_rate: float = 9.0
    tax_2_amount: float = 0.0

    total_tax: float
    grand_total: float
    
    created_at: datetime
    updated_at: datetime
    
    is_template: bool = False
    recurrence: RecurrenceInterval = RecurrenceInterval.NONE
    is_sent: bool = False
    is_paid: bool = False

    class Config:
        populate_by_name = True
