"""App History schemas for application vulnerability history tracking"""
from typing import List
from pydantic import BaseModel, Field


class VulnerabilityCounts(BaseModel):
    """Vulnerability counts by severity"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class MonthlyTrend(BaseModel):
    """Monthly vulnerability trend data"""
    month: str
    quarter: int
    open: int
    closed: int


class YearlyTrend(BaseModel):
    """Yearly vulnerability trend by severity"""
    year: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class CategoryData(BaseModel):
    """Vulnerability data by application category"""
    category: str
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ApplicationHistoryItem(BaseModel):
    """Individual application with vulnerability counts"""
    id: str
    name: str
    category: str
    vulnerabilities: VulnerabilityCounts


class AppHistoryResponse(BaseModel):
    """Complete app history data response"""
    monthlyTrends: List[MonthlyTrend] = Field(default_factory=list, description="Monthly vulnerability trends (open/closed)")
    yearlyTrends: List[YearlyTrend] = Field(default_factory=list, description="Yearly vulnerability trends by severity")
    categoryData: List[CategoryData] = Field(default_factory=list, description="Vulnerabilities grouped by application category")
    applications: List[ApplicationHistoryItem] = Field(default_factory=list, description="List of applications with vulnerability counts")
    totalOpen: int = Field(0, description="Total open vulnerabilities across all months")
    totalClosed: int = Field(0, description="Total closed vulnerabilities across all months")
