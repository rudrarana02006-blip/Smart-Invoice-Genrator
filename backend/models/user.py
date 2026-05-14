from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DEACTIVATED = "deactivated"

class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER
    admin_email: Optional[EmailStr] = None

    @field_validator("password")
    @classmethod
    def truncate_password(cls, v):
        return str(v)[:71] if v else v


class User(UserBase):
    id: str = Field(alias="_id")
    role: UserRole = UserRole.USER
    org_id: Optional[str] = None # For Admins/Independents, this is their own ID. For Users, this is their Admin's ID.
    status: UserStatus = UserStatus.APPROVED
    is_active: bool = True
    is_verified: bool = False
    token_version: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class OTPRequest(BaseModel):
    email: EmailStr
    role: Optional[UserRole] = UserRole.USER
    admin_email: Optional[EmailStr] = None


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class PasswordSet(BaseModel):
    email: EmailStr
    password: str
    token: str
    role: UserRole = UserRole.USER
    admin_email: Optional[EmailStr] = None
    registration_data: Optional[dict] = None

    @field_validator("password")
    @classmethod
    def truncate_password(cls, v):
        return str(v)[:71] if v else v


class PasswordRecoveryRequest(BaseModel):
    email: EmailStr


class PasswordRecoveryReset(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def truncate_password(cls, v):
        return str(v)[:71] if v else v
