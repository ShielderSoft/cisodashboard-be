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
