"""Application schemas for application management"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ApplicationTypeEnum(str, Enum):
    """Application type enumeration - matches ApplicationType in models"""
    WEB_APPLICATION = "web_application"
    MOBILE_APPLICATION = "mobile_application"
    DESKTOP_APPLICATION = "desktop_application"
    API_SERVICE = "api_service"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    THIRD_PARTY = "third_party"


class RiskLevelEnum(str, Enum):
    """Risk level enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class VulnerabilityForApp(BaseModel):
    """Vulnerability data when creating with application"""
    name: str = Field(..., min_length=1, description="Vulnerability name")
    category: str = Field(..., description="Risk category (critical/high/medium/low)")
    description: Optional[str] = Field(None, description="Vulnerability description")


class ApplicationBase(BaseModel):
    """Base application schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Application name")
    type: ApplicationTypeEnum = Field(..., description="Application type")
    description: Optional[str] = Field(None, description="Application description")
    owner: Optional[str] = Field(None, max_length=255, description="Owner name or email")
    vendor: Optional[str] = Field(None, max_length=255, description="Vendor name if third-party")


class ApplicationCreate(ApplicationBase):
    """Schema for creating a new application"""
    vulnerabilities: List[VulnerabilityForApp] = Field(default_factory=list, description="Optional vulnerabilities to create with application")
    version: Optional[str] = Field(None, max_length=50, description="Application version")
    url: Optional[str] = Field(None, max_length=500, description="Application URL")
    risk_level: Optional[RiskLevelEnum] = Field(RiskLevelEnum.MEDIUM, description="Risk level assessment")
    business_criticality: Optional[str] = Field(None, max_length=50, description="Business criticality")


class ApplicationUpdate(BaseModel):
    """Schema for updating an existing application"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[ApplicationTypeEnum] = None
    description: Optional[str] = None
    owner: Optional[str] = Field(None, max_length=255)
    vendor: Optional[str] = Field(None, max_length=255)
    version: Optional[str] = Field(None, max_length=50)
    url: Optional[str] = Field(None, max_length=500)
    risk_level: Optional[RiskLevelEnum] = None
    business_criticality: Optional[str] = Field(None, max_length=50)


class ApplicationResponse(BaseModel):
    """Schema for application response"""
    id: int
    name: str
    type: str  # Application type
    description: Optional[str] = None
    owner: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    url: Optional[str] = None
    risk_level: str = "medium"
    business_criticality: Optional[str] = None
    vulnerabilities_count: int = 0  # Count of associated vulnerabilities
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_vuln_count(cls, application, vuln_count: int = 0):
        """Create response with vulnerability count"""
        return cls(
            id=application.id,
            name=application.name,
            type=application.application_type.value if hasattr(application.application_type, 'value') else str(application.application_type),
            description=application.description,
            owner=application.owner,
            vendor=application.vendor_name,
            version=application.version,
            url=application.url,
            risk_level=application.risk_level.value if hasattr(application.risk_level, 'value') else str(application.risk_level),
            business_criticality=application.business_criticality,
            vulnerabilities_count=vuln_count,
            created_at=application.created_at,
            updated_at=application.updated_at
        )


class ApplicationListResponse(BaseModel):
    """Schema for paginated application list"""
    items: List[ApplicationResponse]
    total: int
    page: int
    size: int
    pages: int


class ApplicationFilterParams(BaseModel):
    """Schema for application filtering parameters"""
    search: Optional[str] = Field(None, description="Search in name, description, owner")
    type: Optional[ApplicationTypeEnum] = Field(None, description="Filter by application type")
    risk_level: Optional[RiskLevelEnum] = Field(None, description="Filter by risk level")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(50, ge=1, le=100, description="Page size")


class ApplicationStatistics(BaseModel):
    """Schema for application statistics"""
    total: int = Field(..., description="Total applications")
    by_type: dict = Field(default_factory=dict, description="Count by application type")
    by_risk_level: dict = Field(default_factory=dict, description="Count by risk level")
    with_vulnerabilities: int = Field(0, description="Applications with vulnerabilities")
    without_vulnerabilities: int = Field(0, description="Applications without vulnerabilities")
