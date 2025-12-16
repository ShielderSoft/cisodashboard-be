from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator

from app.models.models import ComplianceStatus


class VendorCertificateBase(BaseModel):
    """Base certificate schema"""
    certificate_type: str = Field(..., min_length=1, max_length=100, description="Certificate type (e.g., ISO 27001, PCI-DSS)")
    certificate_number: Optional[str] = Field(None, max_length=255)
    issue_date: date = Field(..., description="Certificate issue date")
    expiry_date: date = Field(..., description="Certificate expiry date")
    issuing_authority: Optional[str] = Field(None, max_length=255)
    certificate_url: Optional[str] = Field(None, max_length=500)
    scope: Optional[str] = Field(None, description="Certificate scope")
    notes: Optional[str] = None
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if 'issue_date' in values and v <= values['issue_date']:
            raise ValueError('Expiry date must be after issue date')
        return v


class VendorCertificateCreate(VendorCertificateBase):
    """Schema for creating a certificate"""
    vendor_id: int = Field(..., description="Vendor ID")
    application_id: Optional[int] = Field(None, description="Application ID (optional)")
    status: Optional[ComplianceStatus] = Field(default=ComplianceStatus.COMPLIANT)


class VendorCertificateUpdate(BaseModel):
    """Schema for updating a certificate"""
    certificate_type: Optional[str] = Field(None, max_length=100)
    certificate_number: Optional[str] = Field(None, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[ComplianceStatus] = None
    issuing_authority: Optional[str] = Field(None, max_length=255)
    certificate_url: Optional[str] = Field(None, max_length=500)
    scope: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if v and 'issue_date' in values and values['issue_date'] and v <= values['issue_date']:
            raise ValueError('Expiry date must be after issue date')
        return v


class VendorCertificateResponse(VendorCertificateBase):
    """Schema for certificate response"""
    id: int
    vendor_id: int
    application_id: Optional[int]
    status: ComplianceStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
