"""User schemas"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.models.models import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    profile_type: Optional[str] = None
    privilege_level: Optional[str] = 'standard'
    clearance_level: Optional[str] = 'low'


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str
    is_active: bool = True
    is_superuser: bool = False
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    """Schema for user updates"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    profile_type: Optional[str] = None
    privilege_level: Optional[str] = None
    clearance_level: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_superuser: bool
    role: UserRole
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # keep company/profile_type/privilege/clearance included from base
    
    class Config:
        from_attributes = True