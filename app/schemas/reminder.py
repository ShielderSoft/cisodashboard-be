"""Reminder schemas for application reminder management"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class VulnerabilityCounts(BaseModel):
    """Vulnerability counts by severity"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total: int = 0


class DelayCounts(BaseModel):
    """Delay days by severity"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    max: int = 0  # Maximum delay across all severities


class OwnerApplicationData(BaseModel):
    """Application data for an owner"""
    id: str
    name: str
    vulnerabilities: VulnerabilityCounts
    delay: DelayCounts
    lastReminded: Optional[str] = None
    owner: str


class OwnerReminderData(BaseModel):
    """Reminder data organized by owner"""
    id: str
    name: str
    applicationCount: int
    totalVulnerabilities: int
    applications: List[OwnerApplicationData]


class ApplicationInstanceData(BaseModel):
    """Instance data for an application (owner assignment)"""
    id: str
    owner: str
    vulnerabilities: VulnerabilityCounts
    delay: DelayCounts
    lastReminded: Optional[str] = None


class ApplicationReminderData(BaseModel):
    """Reminder data organized by application"""
    id: str
    name: str
    instances: List[ApplicationInstanceData]


class ReminderStats(BaseModel):
    """Statistics for reminder dashboard"""
    owners: int
    applications: int
    totalVulnerabilities: int


class ReminderResponse(BaseModel):
    """Complete reminder data response"""
    ownerData: List[OwnerReminderData]
    applicationData: List[ApplicationReminderData]
    stats: ReminderStats


class SendReminderRequest(BaseModel):
    """Request to send a reminder"""
    applicationId: int = Field(..., description="Application ID")
    ownerId: Optional[int] = Field(None, description="Owner ID (user ID), if None sends to all owners of the application")


class SendReminderResponse(BaseModel):
    """Response after sending reminder"""
    success: bool
    message: str
    remindedAt: datetime
