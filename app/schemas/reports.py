"""
Reports Module Schemas
This file contains all schemas for the Reports module including Applications and Vulnerabilities
"""
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.models import ApplicationType, RiskLevel, VulnerabilityStatus


# ============= APPLICATION SCHEMAS =============

class ApplicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    application_type: ApplicationType
    version: Optional[str] = None
    url: Optional[str] = None
    risk_level: Optional[RiskLevel] = Field(default=RiskLevel.MEDIUM)
    business_criticality: Optional[str] = None
    data_classification: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    owner_id: Optional[int] = None
    organization_id: Optional[int] = None


class ApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    application_type: Optional[ApplicationType] = None
    version: Optional[str] = None
    url: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    business_criticality: Optional[str] = None
    data_classification: Optional[str] = None


class ApplicationResponse(ApplicationBase):
    id: int
    owner_id: Optional[int]
    organization_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    applications: List[ApplicationResponse]
    total: int
    page: int
    size: int
    pages: int


# ============= VULNERABILITY SCHEMAS =============

class VulnerabilityBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    cve_id: Optional[str] = Field(None, max_length=20)
    severity: RiskLevel
    status: VulnerabilityStatus = Field(default=VulnerabilityStatus.OPEN)
    source: Optional[str] = Field(None, max_length=100)
    cvss_score: Optional[Decimal] = Field(None, ge=0, le=10)
    cvss_vector: Optional[str] = Field(None, max_length=200)
    exploit_available: bool = Field(default=False)
    remediation_plan: Optional[str] = None
    remediation_date: Optional[datetime] = None
    notes: Optional[str] = None


class VulnerabilityCreate(VulnerabilityBase):
    application_id: Optional[int] = None
    vendor_id: Optional[int] = None
    assigned_to_id: Optional[int] = None


class VulnerabilityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    cve_id: Optional[str] = Field(None, max_length=20)
    severity: Optional[RiskLevel] = None
    status: Optional[VulnerabilityStatus] = None
    source: Optional[str] = Field(None, max_length=100)
    cvss_score: Optional[Decimal] = Field(None, ge=0, le=10)
    cvss_vector: Optional[str] = Field(None, max_length=200)
    exploit_available: Optional[bool] = None
    remediation_plan: Optional[str] = None
    remediation_date: Optional[datetime] = None
    notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class VulnerabilityResponse(VulnerabilityBase):
    id: int
    application_id: Optional[int]
    vendor_id: Optional[int]
    assigned_to_id: Optional[int]
    discovered_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VulnerabilityListResponse(BaseModel):
    vulnerabilities: List[VulnerabilityResponse]
    total: int
    page: int
    size: int
    pages: int
