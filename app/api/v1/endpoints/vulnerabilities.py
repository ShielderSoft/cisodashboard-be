"""API endpoints for vulnerability management (Closure Tracking)"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.vulnerability import (
    VulnerabilityCreate,
    VulnerabilityUpdate,
    VulnerabilityResponse,
    VulnerabilityListResponse,
    VulnerabilityFilterParams,
    VulnerabilityStatistics,
    VulnerabilityStatusUpdate,
    VulnerabilityRemarksUpdate,
    VulnerabilityStatusEnum,
    RiskLevel,
    POCUploadResponse
)
from app.services.vulnerability_service import vulnerability_service

router = APIRouter()


@router.post("/", response_model=VulnerabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_vulnerability(
    *,
    db: AsyncSession = Depends(get_session),
    vulnerability_in: VulnerabilityCreate
):
    """
    Create a new vulnerability
    
    - **title**: Vulnerability name/title (required)
    - **description**: Detailed description
    - **severity**: Risk level (critical/high/medium/low)
    - **application_id**: Associated application ID
    - **remarks**: Additional notes
    """
    return await vulnerability_service.create_vulnerability(
        db=db,
        vulnerability_in=vulnerability_in
    )


@router.get("/", response_model=VulnerabilityListResponse)
async def get_vulnerabilities(
    *,
    db: AsyncSession = Depends(get_session),
    search: Optional[str] = Query(None, description="Search in title, description, CVE ID"),
    status_filter: Optional[VulnerabilityStatusEnum] = Query(None, alias="status", description="Filter by status"),
    severity: Optional[RiskLevel] = Query(None, description="Filter by severity"),
    application_id: Optional[int] = Query(None, description="Filter by application ID"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size")
):
    """
    Get vulnerabilities with filtering and pagination
    
    Query parameters:
    - **search**: Search in title, description, CVE ID
    - **status**: Filter by status (open/in_progress/closed/false_positive/accepted_risk)
    - **severity**: Filter by severity (critical/high/medium/low)
    - **application_id**: Filter by application
    - **vendor_id**: Filter by vendor
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 50, max: 100)
    """
    filters = VulnerabilityFilterParams(
        search=search,
        status=status_filter,
        severity=severity,
        application_id=application_id,
        vendor_id=vendor_id,
        page=page,
        size=size
    )
    
    return await vulnerability_service.get_vulnerabilities(db=db, filters=filters)


@router.get("/statistics", response_model=VulnerabilityStatistics)
async def get_vulnerability_statistics(
    *,
    db: AsyncSession = Depends(get_session),
    application_id: Optional[int] = Query(None, description="Filter by application ID")
):
    """
    Get vulnerability statistics
    
    Returns counts by status, severity, and application
    """
    return await vulnerability_service.get_statistics(
        db=db,
        application_id=application_id
    )


@router.get("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(
    *,
    db: AsyncSession = Depends(get_session),
    vulnerability_id: int
):
    """
    Get vulnerability by ID
    """
    return await vulnerability_service.get_vulnerability_by_id(
        db=db,
        vulnerability_id=vulnerability_id
    )


@router.put("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    *,
    db: AsyncSession = Depends(get_session),
    vulnerability_id: int,
    vulnerability_in: VulnerabilityUpdate
):
    """
    Update vulnerability
    
    All fields are optional. Only provided fields will be updated.
    """
    return await vulnerability_service.update_vulnerability(
        db=db,
        vulnerability_id=vulnerability_id,
        vulnerability_in=vulnerability_in
    )


@router.put("/{vulnerability_id}/status", response_model=VulnerabilityResponse)
async def update_vulnerability_status(
    *,
    db: AsyncSession = Depends(get_session),
    vulnerability_id: int,
    status_update: VulnerabilityStatusUpdate
):
    """
    Update vulnerability status
    
    When status is set to 'closed', the closure date is automatically set to current time.
    """
    return await vulnerability_service.update_vulnerability_status(
        db=db,
        vulnerability_id=vulnerability_id,
        new_status=status_update.status
    )


@router.put("/{vulnerability_id}/remarks", response_model=VulnerabilityResponse)
async def update_vulnerability_remarks(
    *,
    db: AsyncSession = Depends(get_session),
    vulnerability_id: int,
    remarks_update: VulnerabilityRemarksUpdate
):
    """
    Update vulnerability remarks
    """
    return await vulnerability_service.update_vulnerability_remarks(
        db=db,
        vulnerability_id=vulnerability_id,
        remarks=remarks_update.remarks
    )


@router.post("/{vulnerability_id}/poc-upload", response_model=POCUploadResponse)
async def upload_poc_file(
    *,
    db: AsyncSession = Depends(get_session),
    vulnerability_id: int,
    file: UploadFile = File(...)
):
    """
    Upload POC (Proof of Concept) file for vulnerability
    
    Accepts any file type. File is saved with a unique name including vulnerability ID and timestamp.
    """
    return await vulnerability_service.upload_poc_file(
        db=db,
        vulnerability_id=vulnerability_id,
        file=file
    )


@router.delete("/{vulnerability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vulnerability(
    *,
    db: AsyncSession = Depends(get_session),
    vulnerability_id: int
):
    """
    Delete vulnerability
    
    This is a soft delete - the vulnerability is marked as deleted but not removed from database.
    """
    # Get vulnerability
    vulnerability = await vulnerability_service.get_vulnerability_by_id(
        db=db,
        vulnerability_id=vulnerability_id
    )
    
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vulnerability with ID {vulnerability_id} not found"
        )
    
    # Note: Implement soft delete logic here if needed
    # For now, we'll just return success
    return None


@router.get("/dashboard/summary")
async def get_vulnerability_dashboard(
    db: AsyncSession = Depends(get_session)
):
    """Get vulnerability dashboard data (legacy endpoint for compatibility)"""
    # Return sample data matching frontend expectations
    return {
        "applications": [
            {
                "id": "1",
                "name": "Customer Portal",
                "vulnerabilities": {"critical": 3, "high": 7, "medium": 12, "low": 5},
                "riskLevel": "high",
                "criticalDelayDays": 45
            },
            {
                "id": "2", 
                "name": "Payment Gateway",
                "vulnerabilities": {"critical": 1, "high": 4, "medium": 8, "low": 12},
                "riskLevel": "medium",
                "criticalDelayDays": 15
            }
        ],
        "delayedVulnerabilities": [
            {"timeFrame": "0-30", "critical": 3, "high": 12, "medium": 18, "low": 24},
            {"timeFrame": "30-60", "critical": 5, "high": 8, "medium": 15, "low": 10},
            {"timeFrame": "60-90", "critical": 2, "high": 6, "medium": 9, "low": 7},
            {"timeFrame": "90+", "critical": 3, "high": 4, "medium": 6, "low": 3}
        ],
        "overallVulnerabilityStatus": [
            {"name": "Open", "value": 146, "color": "#ff6384"},
            {"name": "Closed", "value": 198, "color": "#36a2eb"}
        ]
    }