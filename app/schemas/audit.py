"""
Audit API schemas for dashboard statistics and compliance data
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class AuditStatisticsResponse(BaseModel):
    """Response schema for overall audit statistics"""
    compliant: int = Field(..., description="Number of compliant vendors")
    non_compliant: int = Field(..., description="Number of non-compliant vendors")
    exceptions: int = Field(..., description="Number of vendors with exceptions")
    compliant_trend: float = Field(default=0.0, description="Trend percentage for compliant vendors")
    non_compliant_trend: float = Field(default=0.0, description="Trend percentage for non-compliant vendors")
    exceptions_trend: float = Field(default=0.0, description="Trend percentage for exceptions")

    class Config:
        from_attributes = True


class ComplianceDataResponse(BaseModel):
    """Response schema for compliance data (ISO 27001 or PCI-DSS)"""
    compliant: int = Field(..., description="Number of compliant applications")
    non_compliant: int = Field(..., description="Number of non-compliant applications")
    total: int = Field(..., description="Total number of applications")
    compliant_percentage: float = Field(..., description="Percentage of compliant applications")

    class Config:
        from_attributes = True


class TopVendorItem(BaseModel):
    """Individual vendor item in top vendors list"""
    name: str = Field(..., description="Vendor name")
    compliant: int = Field(..., description="Number of compliant applications")
    non_compliant: int = Field(..., description="Number of non-compliant applications")
    total: int = Field(..., description="Total number of applications")
    compliant_percentage: str = Field(..., description="Compliance percentage as string (e.g., '75')")

    class Config:
        from_attributes = True


class TopVendorsResponse(BaseModel):
    """Response schema for top vendors by application count"""
    vendors: List[TopVendorItem] = Field(..., description="List of top 5 vendors")

    class Config:
        from_attributes = True


# Audit History Schemas

class ComplianceHistoryMonth(BaseModel):
    """Monthly compliance history data point"""
    month: str = Field(..., description="Month name (Jan, Feb, etc.)")
    compliant: int = Field(..., description="Percentage of compliant items")
    nonCompliant: int = Field(..., description="Percentage of non-compliant items")

    class Config:
        from_attributes = True


class TPRMComplianceMonth(BaseModel):
    """Monthly TPRM compliance data point"""
    month: str = Field(..., description="Month name")
    compliant: int = Field(..., description="Percentage of compliant vendors")
    nonCompliant: int = Field(..., description="Percentage of non-compliant vendors")

    class Config:
        from_attributes = True


class ExpiredVendor(BaseModel):
    """Expired vendor information"""
    name: str = Field(..., description="Vendor name")
    expiryDate: str = Field(..., description="Expiry date in YYYY-MM-DD format")

    class Config:
        from_attributes = True


class ExceptionTrendsMonth(BaseModel):
    """Monthly exception trends by risk level"""
    month: str = Field(..., description="Month name")
    critical: int = Field(..., description="Number of critical exceptions")
    high: int = Field(..., description="Number of high exceptions")
    medium: int = Field(..., description="Number of medium exceptions")
    low: int = Field(..., description="Number of low exceptions")

    class Config:
        from_attributes = True


class StandardCompliance(BaseModel):
    """Standard compliance percentages"""
    compliant: int = Field(..., description="Percentage compliant")
    nonCompliant: int = Field(..., description="Percentage non-compliant")

    class Config:
        from_attributes = True


class StandardComplianceData(BaseModel):
    """Compliance data for different standards"""
    iso27001: StandardCompliance = Field(..., description="ISO 27001 compliance")
    pcidss: StandardCompliance = Field(..., description="PCI-DSS compliance")

    class Config:
        from_attributes = True


class AuditHistoryResponse(BaseModel):
    """Complete audit history response"""
    complianceHistory: List[ComplianceHistoryMonth] = Field(..., description="12 months of compliance history")
    tprmCompliance: List[TPRMComplianceMonth] = Field(..., description="12 months of TPRM compliance")
    expiredVendors: List[ExpiredVendor] = Field(..., description="List of expired vendors")
    exceptionTrends: List[ExceptionTrendsMonth] = Field(..., description="12 months of exception trends")
    standardCompliance: StandardComplianceData = Field(..., description="Compliance by standard")

    class Config:
        from_attributes = True
