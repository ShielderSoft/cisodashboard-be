from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum

from app.models.models import RiskLevel, ComplianceStatus


class ComplianceStandardEnum(str, Enum):
    """Compliance standards enum matching frontend options"""
    ISO27001 = "ISO27001"
    PCI_DSS = "PCI_DSS"
    SOX = "SOX"
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOC2 = "SOC2"
    NIST = "NIST"
    COBIT = "COBIT"


# Base Vendor Schemas
class VendorBase(BaseModel):
    """Base vendor schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100, description="Vendor category")
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Vendor name cannot be empty')
        return v.strip()
    
    @validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            return f'https://{v}'
        return v


class VendorCreate(VendorBase):
    """Schema for creating a new vendor"""
    # Additional fields specific to creation
    risk_level: Optional[RiskLevel] = Field(default=RiskLevel.MEDIUM)
    compliance_requirements: Optional[List[ComplianceStandardEnum]] = Field(default_factory=list)
    
    # Contract information
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_value: Optional[float] = Field(None, ge=0)
    
    # Initial compliance standard (matching frontend form)
    standard: Optional[ComplianceStandardEnum] = None
    
    # Application information (from Audit form)
    application_name: Optional[str] = Field(None, max_length=255, description="Application name associated with vendor")
    
    # Certificate information (from Audit form)
    certificate_type: Optional[str] = Field(None, max_length=100, description="Certification type (ISO 27001, PCI-DSS, etc.)")
    certificate_issue_date: Optional[date] = Field(None, description="Certificate start/issue date")
    certificate_expiry_date: Optional[date] = Field(None, description="Certificate expiry date")
    
    @validator('certificate_expiry_date')
    def validate_certificate_dates(cls, v, values):
        if v and 'certificate_issue_date' in values and values['certificate_issue_date']:
            if v <= values['certificate_issue_date']:
                raise ValueError('Certificate expiry date must be after issue date')
        return v
    
    class Config:
        use_enum_values = True


class VendorUpdate(BaseModel):
    """Schema for updating a vendor"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    risk_level: Optional[RiskLevel] = None
    compliance_status: Optional[ComplianceStatus] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_value: Optional[float] = Field(None, ge=0)
    
    # Certificate information
    application_name: Optional[str] = Field(None, max_length=255)
    certificate_type: Optional[str] = Field(None, max_length=100)
    certificate_issue_date: Optional[date] = None
    certificate_expiry_date: Optional[date] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Vendor name cannot be empty')
        return v.strip() if v else None


class VendorResponse(VendorBase):
    """Schema for vendor response"""
    id: int
    risk_level: RiskLevel
    compliance_status: ComplianceStatus
    last_risk_assessment: Optional[date]
    next_risk_assessment: Optional[date]
    contract_start_date: Optional[date]
    contract_end_date: Optional[date]
    contract_value: Optional[float]
    
    # Certificate information
    application_name: Optional[str] = None
    certificate_type: Optional[str] = None
    certificate_issue_date: Optional[date] = None
    certificate_expiry_date: Optional[date] = None
    
    created_at: datetime
    updated_at: datetime
    
    # Compliance metrics
    compliance_rate: Optional[float] = None
    compliant_controls: int = 0
    non_compliant_controls: int = 0
    last_compliance_check: Optional[date] = None
    
    # Related data
    compliance_records_count: Optional[int] = 0
    active_vulnerabilities_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    """Schema for paginated vendor list"""
    vendors: List[VendorResponse]
    total: int
    page: int
    size: int
    pages: int


# Vendor Compliance Schemas
class VendorComplianceBase(BaseModel):
    """Base vendor compliance schema"""
    compliance_area: str = Field(..., min_length=1, max_length=255)
    status: ComplianceStatus
    assessment_date: date
    expiry_date: Optional[date] = None
    certificate_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)


class VendorComplianceCreate(VendorComplianceBase):
    """Schema for creating vendor compliance record"""
    vendor_id: int = Field(..., gt=0)


class VendorComplianceUpdate(BaseModel):
    """Schema for updating vendor compliance record"""
    compliance_area: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[ComplianceStatus] = None
    assessment_date: Optional[date] = None
    expiry_date: Optional[date] = None
    certificate_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)


class VendorComplianceResponse(VendorComplianceBase):
    """Schema for vendor compliance response"""
    id: int
    vendor_id: int
    assessor_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard and Analytics Schemas
class VendorStatsResponse(BaseModel):
    """Vendor statistics for dashboard"""
    total_vendors: int
    compliant_vendors: int
    non_compliant_vendors: int
    pending_assessment: int
    high_risk_vendors: int
    expiring_certificates: int


class VendorRiskDistribution(BaseModel):
    """Vendor risk level distribution"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class VendorComplianceDistribution(BaseModel):
    """Vendor compliance status distribution"""
    compliant: int = 0
    non_compliant: int = 0
    pending: int = 0
    exception: int = 0
    not_applicable: int = 0


class VendorDashboardResponse(BaseModel):
    """Comprehensive vendor dashboard data"""
    stats: VendorStatsResponse
    risk_distribution: VendorRiskDistribution
    compliance_distribution: VendorComplianceDistribution
    recent_vendors: List[VendorResponse]
    expiring_certificates: List[VendorComplianceResponse]


# Search and Filter Schemas
class VendorFilterParams(BaseModel):
    """Query parameters for vendor filtering"""
    search: Optional[str] = Field(None, description="Search in name, description")
    category: Optional[str] = Field(None, max_length=100, description="Filter by category")
    risk_level: Optional[RiskLevel] = None
    compliance_status: Optional[ComplianceStatus] = None
    standard: Optional[ComplianceStandardEnum] = Field(None, description="Filter by compliance standard")
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field("name", description="Sort field")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")


# Bulk Operations Schemas
class VendorBulkUpdateRequest(BaseModel):
    """Schema for bulk vendor updates"""
    vendor_ids: List[int] = Field(..., min_items=1, max_items=100)
    updates: VendorUpdate


class VendorBulkResponse(BaseModel):
    """Response for bulk operations"""
    success_count: int
    failed_count: int
    errors: List[Dict[str, Any]]


# Standard Options Schema (for frontend dropdown)
class StandardOption(BaseModel):
    """Compliance standard option for frontend"""
    value: str
    label: str
    description: Optional[str] = None


class StandardOptionsResponse(BaseModel):
    """Response with all available compliance standards"""
    standards: List[StandardOption]


# Audit and History Schemas
class VendorAuditLogResponse(BaseModel):
    """Vendor audit log entry"""
    id: int
    action: str
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    user_id: Optional[int]
    user_name: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True