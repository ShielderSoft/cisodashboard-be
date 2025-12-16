"""
Audit API endpoints for dashboard statistics and compliance data
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.audit_service import audit_service
from app.schemas.audit import (
    AuditStatisticsResponse,
    ComplianceDataResponse,
    TopVendorsResponse
)

router = APIRouter()


@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    db: AsyncSession = Depends(get_session)
) -> AuditStatisticsResponse:
    """
    Get overall audit statistics
    
    Returns:
        - compliant: Number of compliant vendors
        - non_compliant: Number of non-compliant vendors
        - exceptions: Number of vendors with exceptions
        - trends: Percentage trends for each category
    """
    return await audit_service.get_statistics(db)


@router.get("/iso27001-compliance", response_model=ComplianceDataResponse)
async def get_iso27001_compliance(
    db: AsyncSession = Depends(get_session)
) -> ComplianceDataResponse:
    """
    Get ISO 27001 compliance data for applications
    
    Returns:
        - compliant: Number of ISO 27001 compliant applications
        - non_compliant: Number of non-compliant applications
        - total: Total number of applications
        - compliant_percentage: Percentage of compliant applications
    """
    return await audit_service.get_iso27001_compliance(db)


@router.get("/pcidss-compliance", response_model=ComplianceDataResponse)
async def get_pcidss_compliance(
    db: AsyncSession = Depends(get_session)
) -> ComplianceDataResponse:
    """
    Get PCI-DSS compliance data for applications
    
    Returns:
        - compliant: Number of PCI-DSS compliant applications
        - non_compliant: Number of non-compliant applications
        - total: Total number of applications
        - compliant_percentage: Percentage of compliant applications
    """
    return await audit_service.get_pcidss_compliance(db)


@router.get("/top-vendors", response_model=TopVendorsResponse)
async def get_top_vendors(
    db: AsyncSession = Depends(get_session),
    limit: int = 5
) -> TopVendorsResponse:
    """
    Get top vendors by certificate count with compliance breakdown
    
    Args:
        limit: Number of top vendors to return (default: 5)
    
    Returns:
        List of top vendors with:
        - name: Vendor name
        - compliant: Number of valid (active, non-expired) certificates
        - non_compliant: Number of invalid certificates
        - total: Total number of certificates
        - compliant_percentage: Compliance percentage as string
    """
    return await audit_service.get_top_vendors(db, limit=limit)
