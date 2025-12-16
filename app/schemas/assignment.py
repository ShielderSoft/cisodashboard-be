from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class AssignmentCreate(BaseModel):
    name: str
    description: Optional[str]
    vendor_id: Optional[int]
    standard_id: Optional[int]
    due_date: Optional[date]


class AssignmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    vendor_id: Optional[int]
    standard_id: Optional[int]
    due_date: Optional[date]

    class Config:
        orm_mode = True


class AssessmentResponse(BaseModel):
    id: int
    vendor_id: int
    assignment_id: int
    control_identifier: Optional[str]
    statement: Optional[str]  # Full control statement/title from ComplianceRequirement
    section: Optional[str]  # Category from ComplianceRequirement
    compliant: bool
    remark: Optional[str]
    poc: Optional[str]
    status: Optional[str]

    class Config:
        orm_mode = True


class AssessmentUpdate(BaseModel):
    """Schema for updating assessment"""
    compliant: Optional[bool]
    remark: Optional[str]
    poc: Optional[str]
    status: Optional[str]  # implemented, partiallyImplemented, notImplemented, notApplicable
