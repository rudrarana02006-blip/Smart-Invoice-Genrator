"""
Client Pydantic models — request/response schemas.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class ClientCreate(BaseModel):
    """Schema for creating a new client."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    company_name: Optional[str] = None
    gstin: Optional[str] = None
    
    # Default Tax Settings for this client
    default_cgst_rate: float = Field(default=0, ge=0)
    default_sgst_rate: float = Field(default=0, ge=0)


class ClientUpdate(BaseModel):
    """Schema for updating an existing client."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company_name: Optional[str] = None
    gstin: Optional[str] = None
    default_cgst_rate: Optional[float] = Field(None, ge=0)
    default_sgst_rate: Optional[float] = Field(None, ge=0)


class ClientInDB(ClientCreate):
    """Schema representing a client stored in the database."""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
