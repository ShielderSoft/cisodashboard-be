"""EOSL (End of Service Life) schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class EOSLType(str, Enum):
    """EOSL Type enum"""
    EOS = "EOS"  # End of Support
    EOL = "EOL"  # End of Life


class EOSLAssetBase(BaseModel):
    """Base EOSL Asset schema"""
    asset_name: str = Field(..., description="Name of the asset")
    owner: str = Field(..., description="Owner of the asset")
    asset_type: str = Field(..., description="Type of asset (Server, Router, etc.)")
    eosl_type: EOSLType = Field(..., description="EOSL type (EOS or EOL)")
    eosl_date: date = Field(..., description="End of Service Life date")
    remark: Optional[str] = Field(None, description="Additional remarks")
    reminder_sent: bool = Field(default=False, description="Whether reminder has been sent")


class EOSLAssetCreate(EOSLAssetBase):
    """Schema for creating EOSL asset"""
    pass


class EOSLAssetUpdate(BaseModel):
    """Schema for updating EOSL asset"""
    asset_name: Optional[str] = None
    owner: Optional[str] = None
    asset_type: Optional[str] = None
    eosl_type: Optional[EOSLType] = None
    eosl_date: Optional[date] = None
    remark: Optional[str] = None
    reminder_sent: Optional[bool] = None


class EOSLAssetResponse(EOSLAssetBase):
    """Schema for EOSL asset response"""
    id: int
    asset_id: str  # Format: ASSET-0001
    days_until_eosl: Optional[int] = Field(None, description="Days until EOSL date")
    created_at: datetime
    updated_at: datetime
    
    # Frontend-friendly camelCase fields
    assetName: Optional[str] = None
    assetType: Optional[str] = None
    eoslType: Optional[str] = None
    eoslDate: Optional[str] = None
    reminderSent: Optional[bool] = None
    daysUntil: Optional[int] = None
    
    class Config:
        from_attributes = True


class EOSLAssetListResponse(BaseModel):
    """Schema for list of EOSL assets with pagination"""
    items: List[EOSLAssetResponse]
    total: int
    page: int
    size: int
    pages: int


class TopNonCompliantAsset(BaseModel):
    """Schema for top non-compliant assets by type"""
    name: str = Field(..., description="Asset type name")
    count: int = Field(..., description="Number of assets")


class ComplianceMonthData(BaseModel):
    """Schema for monthly compliance data"""
    month: str = Field(..., description="Month abbreviation (Jan, Feb, etc.)")
    compliant: int = Field(..., description="Compliant percentage")
    nonCompliant: int = Field(..., description="Non-compliant percentage")


class EOSLSummary(BaseModel):
    """Schema for EOSL summary statistics"""
    eosCount: int = Field(..., description="Count of EOS assets")
    eolCount: int = Field(..., description="Count of EOL assets")
    totalAssets: int = Field(..., description="Total number of assets")
    expiringSoon: int = Field(default=0, description="Assets expiring within 30 days")
    expired: int = Field(default=0, description="Assets already expired")


class EOSLDashboardResponse(BaseModel):
    """Schema for complete EOSL dashboard data"""
    assets: List[EOSLAssetResponse]
    topNonCompliantAssets: List[TopNonCompliantAsset]
    complianceByYear: dict = Field(..., description="Compliance data by year")
    summary: EOSLSummary
    currentDateTime: str
    currentUser: str


class AssetUploadRequest(BaseModel):
    """Schema for bulk asset upload"""
    assets: List[EOSLAssetCreate]
    
    
class AssetUploadResponse(BaseModel):
    """Schema for bulk upload response"""
    success: bool
    created: int
    failed: int
    errors: Optional[List[str]] = None
