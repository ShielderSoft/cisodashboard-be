"""
Activity Log Schemas
Pydantic models for activity log validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ActivityTypeEnum(str, Enum):
    """Activity types matching the database enum"""
    APPLICATION_CREATED = "application_created"
    APPLICATION_UPDATED = "application_updated"
    APPLICATION_DELETED = "application_deleted"
    VENDOR_CREATED = "vendor_created"
    VENDOR_UPDATED = "vendor_updated"
    VENDOR_DELETED = "vendor_deleted"
    CERTIFICATE_ADDED = "certificate_added"
    CERTIFICATE_UPDATED = "certificate_updated"
    CERTIFICATE_EXPIRED = "certificate_expired"
    CERTIFICATE_EXPIRING_SOON = "certificate_expiring_soon"
    VULNERABILITY_CREATED = "vulnerability_created"
    VULNERABILITY_UPDATED = "vulnerability_updated"
    VULNERABILITY_CLOSED = "vulnerability_closed"
    VULNERABILITY_REOPENED = "vulnerability_reopened"
    COMPLIANCE_CHECK_COMPLETED = "compliance_check_completed"
    COMPLIANCE_STATUS_CHANGED = "compliance_status_changed"
    EXCEPTION_CREATED = "exception_created"
    EXCEPTION_APPROVED = "exception_approved"
    EXCEPTION_REJECTED = "exception_rejected"
    EXCEPTION_EXPIRED = "exception_expired"
    EOSL_ASSET_ADDED = "eosl_asset_added"
    EOSL_ASSET_EXPIRED = "eosl_asset_expired"
    EOSL_ASSET_EXPIRING_SOON = "eosl_asset_expiring_soon"
    USER_LOGIN = "user_login"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    AUDIT_COMPLETED = "audit_completed"
    AUDIT_FAILED = "audit_failed"
    SYSTEM_ALERT = "system_alert"
    DATA_EXPORT = "data_export"
    REPORT_GENERATED = "report_generated"


class ActivityPriorityEnum(str, Enum):
    """Activity priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityLogBase(BaseModel):
    """Base schema for activity log"""
    activity_type: ActivityTypeEnum
    priority: ActivityPriorityEnum = ActivityPriorityEnum.MEDIUM
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    entity_type: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[int] = None
    entity_name: Optional[str] = Field(None, max_length=255)
    extra_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ActivityLogCreate(ActivityLogBase):
    """Schema for creating a new activity log entry"""
    pass


class ActivityLogUpdate(BaseModel):
    """Schema for updating activity log (limited fields)"""
    is_read: Optional[bool] = None
    status: Optional[str] = Field(None, max_length=50)


class ActivityLogResponse(ActivityLogBase):
    """Schema for activity log API response"""
    id: int
    status: str
    is_read: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ActivityLogListResponse(BaseModel):
    """Schema for paginated activity log list"""
    items: List[ActivityLogResponse]
    total: int
    page: int
    size: int
    pages: int


class ActivityStatistics(BaseModel):
    """Statistics about activities"""
    total_activities: int
    unread_count: int
    by_priority: Dict[str, int]
    by_type: Dict[str, int]
    recent_24h: int
    recent_7d: int


class ActivityFilter(BaseModel):
    """Filters for querying activities"""
    activity_type: Optional[List[ActivityTypeEnum]] = None
    priority: Optional[List[ActivityPriorityEnum]] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    is_read: Optional[bool] = None
    days: Optional[int] = Field(7, ge=1, le=365)  # Default last 7 days
    tags: Optional[List[str]] = None
