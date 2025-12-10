from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

# --- Company Schemas ---
class CompanyBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None

class CompanyCreate(CompanyBase):
    companyId: str = Field(..., description="Unique slug for the company (e.g., acme-law)")

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None

class Company(CompanyBase):
    companyId: str
    status: str = "active"
    createdAt: str

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "admin"

class UserCreate(UserBase):
    allowedClients: Optional[list[str]] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    allowedClients: Optional[list[str]] = None

class User(UserBase):
    companyId: str
    userId: str
    status: str = "active"
    allowedClients: Optional[list[str]] = []
    allowedClients: Optional[list[str]] = []
    createdAt: str
    archived: bool = False
