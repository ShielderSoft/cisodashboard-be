from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class ExceptionCategoryEnum(str, Enum):
    """Exception category enumeration for API"""
    COMPLIANCE = "compliance"
    TECHNICAL = "technical" 
    OPERATIONAL = "operational"
    OTHER = "other"


class ExceptionSeverityEnum(str, Enum):
    """Exception severity enumeration for API"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExceptionStatusEnum(str, Enum):
    """Exception status enumeration for API"""
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"


# Base Exception Schema
class ExceptionBase(BaseModel):
    """Base exception schema"""
    exception_name: str = Field(..., min_length=1, max_length=255, description="Name of the exception")
    category: ExceptionCategoryEnum = Field(..., description="Exception category")
    severity: ExceptionSeverityEnum = Field(..., description="Exception severity level")
    status: ExceptionStatusEnum = Field(default=ExceptionStatusEnum.PENDING, description="Exception status")
    start_date: date = Field(..., description="Exception start date")
    end_date: Optional[date] = Field(None, description="Exception end date")
    comments: Optional[str] = Field(None, max_length=2000, description="Additional comments")
    risk_assessment: Optional[str] = Field(None, max_length=2000, description="Risk assessment details")
    mitigation_plan: Optional[str] = Field(None, max_length=2000, description="Mitigation plan")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('exception_name')
    def validate_exception_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Exception name cannot be empty')
        return v.strip()


# Exception Create Schema
class ExceptionCreate(ExceptionBase):
    """Schema for creating an exception"""
    organization_id: Optional[int] = Field(None, description="Organization ID")
    assigned_to_id: Optional[int] = Field(None, description="User ID to assign exception to")


# Exception Update Schema 
class ExceptionUpdate(BaseModel):
    """Schema for updating an exception"""
    exception_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[ExceptionCategoryEnum] = None
    severity: Optional[ExceptionSeverityEnum] = None
    status: Optional[ExceptionStatusEnum] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    comments: Optional[str] = Field(None, max_length=2000)
    risk_assessment: Optional[str] = Field(None, max_length=2000)
    mitigation_plan: Optional[str] = Field(None, max_length=2000)
    assigned_to_id: Optional[int] = None
    approval_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('exception_name')
    def validate_exception_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Exception name cannot be empty')
        return v.strip() if v else v


# Exception Response Schema
class ExceptionResponse(ExceptionBase):
    """Schema for exception response"""
    id: int
    approval_status: Optional[str] = None
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    organization_id: Optional[int] = None
    created_by_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Additional computed fields
    is_expired: Optional[bool] = Field(None, description="Whether the exception has expired")
    days_remaining: Optional[int] = Field(None, description="Days until exception expires")

    class Config:
        from_attributes = True


# Exception List Response Schema
class ExceptionListResponse(BaseModel):
    """Schema for paginated exception list"""
    exceptions: List[ExceptionResponse]
    total: int
    page: int
    size: int
    pages: int


# Exception Filters Schema
class ExceptionFilters(BaseModel):
    """Schema for filtering exceptions"""
    category: Optional[ExceptionCategoryEnum] = None
    severity: Optional[ExceptionSeverityEnum] = None
    status: Optional[ExceptionStatusEnum] = None
    search: Optional[str] = Field(None, max_length=255, description="Search in exception name and comments")
    organization_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    created_by_id: Optional[int] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None
    approval_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")


# Exception Statistics Schema
class ExceptionStats(BaseModel):
    """Schema for exception statistics"""
    total_exceptions: int
    active_exceptions: int
    expired_exceptions: int
    pending_exceptions: int
    by_category: dict
    by_severity: dict
    expiring_soon: int = Field(description="Exceptions expiring within 30 days")


# Exception Categories Schema (for frontend dropdowns)
class ExceptionCategoriesResponse(BaseModel):
    """Schema for exception categories"""
    categories: List[dict] = Field(
        default=[
            {"value": "compliance", "label": "Compliance"},
            {"value": "technical", "label": "Technical"},
            {"value": "operational", "label": "Operational"},
            {"value": "other", "label": "Other"}
        ]
    )
    severities: List[dict] = Field(
        default=[
            {"value": "critical", "label": "Critical"},
            {"value": "high", "label": "High"},
            {"value": "medium", "label": "Medium"},
            {"value": "low", "label": "Low"}
        ]
    )
    statuses: List[dict] = Field(
        default=[
            {"value": "active", "label": "Active"},
            {"value": "expired", "label": "Expired"},
            {"value": "pending", "label": "Pending"}
        ]
    )