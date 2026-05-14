"""
Profile Pydantic models — request/response schemas for Company Profiles.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BankAccount(BaseModel):
    bank_name: str = Field(..., min_length=1)
    account_no: str = Field(..., min_length=1)
    ifsc: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)

class CompanyProfile(BaseModel):
    company_name: str = Field(..., min_length=1)
    company_tagline: Optional[str] = None
    address: str = Field(..., min_length=1)
    country: str = Field(default="India", min_length=1)
    gstin: Optional[str] = None
    vat_number: Optional[str] = None
    pan: Optional[str] = None
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    website: Optional[str] = None
    
    # Bank Details
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account_name: Optional[str] = None

    # Multiple Bank Details (Optional)
    bank_accounts: List[BankAccount] = []


class CompanyProfileInDB(CompanyProfile):
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
