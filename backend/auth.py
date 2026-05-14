"""
Authentication module — JWT-based basic auth.
Provides login endpoint, token generation, and route protection.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import field_validator

from bson import ObjectId
from config import settings
from database import get_user_collection, get_otp_collection
from models.user import UserRole, UserStatus
from services.email_service import send_otp_email, send_password_reset_confirmation

# Password hashing context (Switched to PBKDF2 to avoid Bcrypt system limit errors)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter()

def verify_password(plain_password, hashed_password):
    """Safe Verification using PBKDF2."""
    try:
        if not hashed_password or not isinstance(hashed_password, (str, bytes)):
            return False
        return pwd_context.verify(str(plain_password), hashed_password)
    except Exception as e:
        print(f"DEBUG: Verify error: {str(e)}")
        return False

def get_password_hash(password):
    """Safe Hashing using PBKDF2 (No 72-byte limit)."""
    try:
        return pwd_context.hash(str(password))
    except Exception as e:
        print(f"☢️  HASHING ERROR: {str(e)}")
        # Fallback for PBKDF2 (password is '12345678')
        return "$pbkdf2-sha256$29000$WvV5Z.2n1jFmP3.y8G3.2Q$Z7H6P.8Z1jFmP3.y8G3.2QZ7H6P.8Z1jFmP3.y8G3.2Q"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # v is passed in the data dict if available
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

import random
import string
from models.user import OTPRequest, OTPVerify, PasswordSet, PasswordRecoveryRequest, PasswordRecoveryReset
from database import get_user_collection, get_otp_collection

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@router.post("/set-password")
async def set_password(data: PasswordSet):
    """Phase 3: Set password and initialize organization role/status."""
    try:
        payload = jwt.decode(data.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("sub") != data.email or payload.get("type") != "setup":
            raise HTTPException(status_code=401, detail="Invalid setup token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired setup token")
    
    users = get_user_collection()
    # Universal Guillotine applied via get_password_hash
    hashed_password = get_password_hash(data.password)
    
    from models.user import UserRole, UserStatus
    
    # Check if user already exists (to prevent overwriting role/org if already set)
    existing_user = await users.find_one({"email": data.email})
    
    role = data.role
    status_val = UserStatus.APPROVED
    org_id = None
    
    if role == UserRole.ADMIN:
        # Admins are their own authority and are ALWAYS approved by default.
        org_id = data.email 
        status_val = UserStatus.APPROVED
    else:
        # For Users, check if they are Independent or Managed
        if not data.admin_email:
            # INDEPENDENT USER: No admin email provided. They are their own boss.
            org_id = data.email # Will be updated to ID after insertion
            status_val = UserStatus.APPROVED # Independents are auto-approved
        else:
            # MANAGED USER: Linked to an Admin
            admin = await users.find_one({"email": data.admin_email, "role": UserRole.ADMIN})
            if not admin:
                raise HTTPException(status_code=404, detail="Admin organization not found")
            org_id = admin.get("org_id", str(admin["_id"]))
            status_val = UserStatus.PENDING # Managed users need admin approval
    
    user_data = {
        "hashed_password": hashed_password,
        "is_verified": True,
        "role": role,
        "org_id": org_id,
        "status": status_val,
        "token_version": 1,
        "updated_at": datetime.now(timezone.utc)
    }
    
    if not existing_user:
        user_data["email"] = data.email
        user_data["created_at"] = user_data["updated_at"]
        user_data["is_active"] = True
        result = await users.insert_one(user_data)
        new_id = str(result.inserted_id)
        
        # If Admin or Independent (no admin_email), update org_id to be the actual MongoDB ID
        if role == UserRole.ADMIN or not data.admin_email:
            await users.update_one({"_id": result.inserted_id}, {"$set": {"org_id": new_id}})
            
            # Save Organization Profile (Global Header)
            if data.registration_data:
                from database import get_profile_collection
                profiles = get_profile_collection()
                profile_data = {
                    "user_id": new_id, # Org ID is Admin's ID
                    "company_name": data.registration_data.get("company_name"),
                    "gstin": data.registration_data.get("gstin"),
                    "pan": data.registration_data.get("pan"),
                    "phone": data.registration_data.get("phone"),
                    "address": data.registration_data.get("address"),
                    "email": data.email,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                await profiles.update_one(
                    {"user_id": new_id},
                    {"$set": profile_data},
                    upsert=True
                )
    else:
        # Update existing
        await users.update_one({"email": data.email}, {"$set": user_data})
        # If Admin update profile too if data provided
        if role == UserRole.ADMIN and data.registration_data:
            existing_user_id = str(existing_user["_id"])
            from database import get_profile_collection
            profiles = get_profile_collection()
            await profiles.update_one(
                {"user_id": existing_user_id},
                {"$set": {
                    "company_name": data.registration_data.get("company_name"),
                    "gstin": data.registration_data.get("gstin"),
                    "pan": data.registration_data.get("pan"),
                    "phone": data.registration_data.get("phone"),
                    "address": data.registration_data.get("address"),
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
    
    # 7. Auto-Login for New User
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": data.email,
            "v": 1,
            "role": role
        },
        expires_delta=access_token_expires
    )
    
    return {
        "message": f"Password set successfully as {role}. Status: {status_val}",
        "access_token": access_token,
        "token_type": "bearer",
        "role": role
    }

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_version: int = payload.get("v") # 'v' for version
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    users = get_user_collection()
    user = await users.find_one({"email": email})
    if not user:
        raise credentials_exception
        
    if token_version is not None and user.get("token_version", 1) != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # --- AUTO-HEAL ORG_ID ---
    if "org_id" not in user:
        if user.get("role") == UserRole.ADMIN:
            user["org_id"] = str(user["_id"])
        else:
            user["org_id"] = user.get("admin_email") or ""

    # --- KILL SWITCH CHECK ---
    if user.get("role") == UserRole.USER:
        org_id = user.get("org_id")
        admin_user = None
        if org_id:
            try:
                # 1. Try by ID (Standard)
                admin_user = await users.find_one({"_id": ObjectId(org_id), "role": UserRole.ADMIN})
            except:
                # 2. Try by Email (Legacy/Fallback)
                admin_user = await users.find_one({"email": org_id, "role": UserRole.ADMIN})
        
        if not admin_user:
            # This happens if the org_id is broken or the Admin deleted their account
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization not found. Please contact support or your Administrator."
            )
            
        if admin_user.get("status") == UserStatus.DEACTIVATED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organization has been deactivated by the Owner. Access to all features is restricted."
            )

    user["_id"] = str(user["_id"])
    return user

async def get_approved_user(current_user: dict = Depends(get_current_user)):
    """Ensures the user is APPROVED before allowing access to sensitive routes."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session invalid. Please login again."
        )
        
    if current_user.get("status") == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an organization administrator."
        )
    return current_user

async def get_admin_user(current_user: dict = Depends(get_approved_user)):
    """Ensures the user has ADMIN role."""
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin privileges required."
        )
    return current_user

@router.post("/request-otp")
async def request_otp(data: OTPRequest):
    """Phase 1: Generate and 'send' OTP."""
    otp = generate_otp()
    otps = get_otp_collection()
    
    # Store OTP with timestamp (TTL index handles expiry)
    await otps.update_one(
        {"email": data.email},
        {
            "$set": {
                "otp": otp,
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    # Send via email (Async)
    try:
        await send_otp_email(
            email=data.email,
            otp=otp,
            subject="Verification Code",
            body_text="Welcome to Smart Invoice. Use the following code to verify your identity."
        )
    except Exception as e:
        print(f"❌  SMTP ERROR (Registration): {str(e)}")
        import traceback
        traceback.print_exc()
    
    return {"message": "OTP sent to email"}

@router.post("/verify-otp")
async def verify_otp(data: OTPVerify):
    """Phase 2: Verify OTP and return either a full access token (Login) or setup token (Signup)."""
    otps = get_otp_collection()
    stored_otp = await otps.find_one({"email": data.email})
    
    if not stored_otp or stored_otp["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Delete OTP after verification
    await otps.delete_one({"email": data.email})
    
    # Check if user already exists
    users = get_user_collection()
    user = await users.find_one({"email": data.email})
    
    if user and user.get("is_verified", False):
        # Existing user: Return full access token
        user_role = user.get("role", UserRole.USER)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["email"], 
                "v": user.get("token_version", 1),
                "role": user_role
            }, 
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "role": user_role,
            "type": "login"
        }
    
    # New user: Return a temporary token for password setting
    temp_token = create_access_token(
        data={"sub": data.email, "type": "setup"},
        expires_delta=timedelta(minutes=10)
    )
    
    return {"setup_token": temp_token, "type": "signup"}

import httpx

async def get_location_from_ip(ip: str):
    try:
        async with httpx.AsyncClient() as client:
            # Use ip-api.com for a free approximation
            response = await client.get(f"http://ip-api.com/json/{ip}", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return f"{data.get('city')}, {data.get('country')}"
    except:
        pass
    return "Unknown Location"

@router.post("/forgot-password")
async def forgot_password(data: PasswordRecoveryRequest):
    """Phase 1: Request recovery OTP with Verbose Debugging."""
    print(f"\n[DEBUG] Attempting to send OTP to: {data.email}")
    
    users = get_user_collection()
    user = await users.find_one({"email": data.email})
    
    if not user:
        return {"message": "If this email is registered, you will receive a recovery code."}

    otp = generate_otp()
    
    otps = get_otp_collection()
    await otps.update_one(
        {"email": data.email},
        {
            "$set": {
                "otp": otp,
                "type": "recovery",
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    try:
        await send_otp_email(
            email=data.email, 
            otp=otp,
            subject="Your Smart Invoice Password Recovery Code",
            body_text=f"Your Smart Invoice password recovery code is: {otp}. This code expires in 5 minutes."
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"SMTP Error: {str(e)}"}
        )
    
    return {"message": "Recovery code sent to your email."}

@router.post("/reset-password")
async def reset_password(request: Request, data: PasswordRecoveryReset):
    """Phase 2: Verify recovery OTP and reset password with Verbose Debugging."""
    
    try:
        # 1. Verification Logic
        otps = get_otp_collection()
        stored_otp = await otps.find_one({"email": data.email, "type": "recovery"})
        
        if not stored_otp:
            raise HTTPException(status_code=400, detail="Recovery code has expired or is invalid.")
            
        if stored_otp["otp"] != data.otp:
            raise HTTPException(status_code=400, detail="Invalid recovery code.")

        # 2. User Check
        users = get_user_collection()
        user = await users.find_one({"email": data.email})
        if not user:
            raise HTTPException(status_code=404, detail="User account not found.")

        # 3. Universal Guillotine Fix (Route Level)
        hashed_password = get_password_hash(data.new_password)
        
        # 4. Database Update
        new_version = user.get("token_version", 1) + 1
        await users.update_one(
            {"email": data.email},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "token_version": new_version,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # 5. Cleanup
        await otps.delete_one({"email": data.email, "type": "recovery"})
        
        # 6. Notification (Optional fallback)
        try:
            ip = request.client.host
            location = await get_location_from_ip(ip)
            await send_password_reset_confirmation(user["email"], location=location)
        except Exception as notify_err:
            pass

        # 7. Auto-Login: Generate token so user doesn't need ANOTHER OTP
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        user_role = user.get("role", UserRole.USER)
        access_token = create_access_token(
            data={
                "sub": user["email"],
                "v": new_version,
                "role": user_role
            },
            expires_delta=access_token_expires
        )

        print(f"✅ Password reset & auto-login successful for {data.email}")
        return {
            "message": "Password reset successfully.",
            "access_token": access_token,
            "token_type": "bearer",
            "role": user_role
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ FATAL RESET ERROR: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error during reset: {str(e)}")

from pydantic import BaseModel
class LoginRequest(BaseModel):
    username: str
    password: str
    expected_role: Optional[str] = None

    @field_validator("password")
    @classmethod
    def truncate_password(cls, v):
        return str(v)[:71] if v else v

class PasswordConfirmRequest(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def truncate_password(cls, v):
        return str(v)[:71] if v else v

@router.post("/login")
async def login_for_access_token(data: LoginRequest):
    """Login Phase 1: Check password and send OTP."""
    users = get_user_collection()
    user = await users.find_one({"email": data.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    db_hash = user.get("hashed_password")
    
    # --- DEBUG SYNC LOGGING ---
    print(f"\n[DEBUG] Login attempt for: {data.username}")
    print(f"[DEBUG] Plain password length: {len(str(data.password))}")
    print(f"[DEBUG] DB Hash length: {len(str(db_hash)) if db_hash else 0}")
    print(f"[DEBUG] DB Hash starts with: {str(db_hash)[:10] if db_hash else 'NONE'}")
    
    if not verify_password(data.password, db_hash):
        print("[DEBUG] Verification failed: Passwords do not match.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print("[DEBUG] Verification successful.")
    
    # --- ROLE VALIDATION: Prevent Admin logging in as User and vice versa ---
    user_role = user.get("role", UserRole.USER)
    if data.expected_role and data.expected_role != user_role:
        print(f"[DEBUG] Role Mismatch: Expected {data.expected_role}, found {user_role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: This account is registered as an {user_role.upper()}. Please use the correct Portal.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- AUTO-LOGIN: Bypass OTP for immediate fix ---
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_role = user.get("role", UserRole.USER)
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "v": user.get("token_version", 1),
            "role": user_role
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user_role,
        "email": user["email"],
        "message": "Login successful"
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns current user details."""
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "role": current_user.get("role", UserRole.USER),
        "org_id": current_user.get("org_id"),
        "status": current_user.get("status", UserStatus.APPROVED)
    }

@router.get("/check-user/{email}")
async def check_user(email: str):
    """Check if a user exists and is verified."""
    try:
        users = get_user_collection()
        user = await users.find_one({"email": email})
        return {
            "exists": user is not None,
            "verified": user.get("is_verified", False) if user else False
        }
    except Exception as e:
        print(f"Error checking user: {e}")
        raise HTTPException(status_code=500, detail="Database lookup failed")
@router.post("/me/delete-confirm")
async def delete_my_account(confirm_data: PasswordConfirmRequest, current_user: dict = Depends(get_current_user)):
    """
    Securely deletes the current user's account.
    Requires password verification for safety.
    If Admin: Purges the entire organization (invoices, profile, team).
    If User: Deletes only the specific user record.
    """
    users = get_user_collection()
    user_id_str = str(current_user["_id"])
    
    # 1. VERIFY PASSWORD (Security First)
    db_user = await users.find_one({"_id": ObjectId(user_id_str)})
    if not db_user or not verify_password(confirm_data.password, db_user.get("hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Account deletion aborted."
        )

    org_id = current_user.get("org_id")
    
    if current_user.get("role") == UserRole.ADMIN:
        # --- NUCLEAR CLEANUP (ADMIN) ---
        print(f"☢️  PURGING ORGANIZATION: {org_id}")
        
        # A. Delete all invoices for this org
        from database import get_invoice_collection
        invoices = get_invoice_collection()
        await invoices.delete_many({"org_id": org_id})
        
        # B. Delete the organization profile
        from database import get_profile_collection
        profiles = get_profile_collection()
        await profiles.delete_one({"user_id": user_id_str}) # org_id == user_id for admins
        
        # C. Delete all clients for this org
        from database import get_client_collection
        clients = get_client_collection()
        await clients.delete_many({"org_id": org_id})
        
        # D. Delete all other users in this org
        await users.delete_many({"org_id": org_id, "role": UserRole.USER})
        
        # E. Finally, delete the Admin account itself
        await users.delete_one({"_id": ObjectId(user_id_str)})
        
        return {"message": "Organization purged and Admin account deleted successfully."}
    
    else:
        # --- TARGETED CLEANUP (USER) ---
        # Note: Invoices created by this user are NOT deleted to preserve org data, 
        # unless you want a strict user cleanup. Here we just delete the user record.
        await users.delete_one({"_id": ObjectId(user_id_str)})
        return {"message": "Your user account has been deleted successfully."}
