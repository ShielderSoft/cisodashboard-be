"""Dashboard schemas for main vulnerability dashboard"""
from typing import List, Optional
from pydantic import BaseModel, Field


class VulnerabilityCounts(BaseModel):
    """Vulnerability counts by severity"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ApplicationVulnerability(BaseModel):
    """Application with vulnerability counts"""
    id: str
    name: str
    vulnerabilities: VulnerabilityCounts
    riskLevel: str  # 'high', 'medium', 'low'
    criticalDelayDays: int = 0


class DelayedVulnerabilityTimeFrame(BaseModel):
    """Delayed vulnerabilities grouped by time frame"""
    timeFrame: str  # '0-30', '30-60', '60-90', '90+'
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class VulnerabilityStatus(BaseModel):
    """Overall vulnerability status (pie chart)"""
    name: str  # 'Open' or 'Closed'
    value: int
    color: str


class ApplicationTypeVulnerabilities(BaseModel):
    """Vulnerabilities by application type (Internal/External)"""
    type: str  # 'Internal' or 'External'
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class DetailedVulnerabilityBreakdown(BaseModel):
    """Detailed vulnerability breakdown for an application"""
    id: str
    name: str
    open: VulnerabilityCounts
    closed: VulnerabilityCounts


class DashboardDataResponse(BaseModel):
    """Complete dashboard data response"""
    applications: List[ApplicationVulnerability] = Field(default_factory=list, description="List of applications with vulnerability counts")
    delayedVulnerabilities: List[DelayedVulnerabilityTimeFrame] = Field(default_factory=list, description="Delayed vulnerabilities by time frame")
    overallVulnerabilityStatus: List[VulnerabilityStatus] = Field(default_factory=list, description="Overall open vs closed status")
    applicationTypeVulnerabilities: List[ApplicationTypeVulnerabilities] = Field(default_factory=list, description="Vulnerabilities by application type")
    detailedVulnerabilities: List[DetailedVulnerabilityBreakdown] = Field(default_factory=list, description="Detailed breakdown by application")
