from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_session
from app.services.dashboard_service import dashboard_service
from app.schemas.dashboard import DashboardDataResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/data", response_model=DashboardDataResponse)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_session)
):
    """
    Get complete dashboard data for the main vulnerability dashboard
    
    Returns:
        DashboardDataResponse with all dashboard components:
        - applications: List of applications with vulnerability counts
        - delayedVulnerabilities: Vulnerabilities grouped by time frame
        - overallVulnerabilityStatus: Open vs closed vulnerability counts
        - applicationTypeVulnerabilities: Vulnerabilities by app type (internal/external)
        - detailedVulnerabilities: Detailed breakdown by application
    """
    try:
        dashboard_data = await dashboard_service.get_dashboard_data(db)
        return dashboard_data
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )


@router.get("/")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_session)
):
    """Get main dashboard summary (legacy endpoint)"""
    return {
        "summary": {
            "totalApplications": 47,
            "totalVulnerabilities": 344,
            "openVulnerabilities": 146,
            "closedVulnerabilities": 198,
            "criticalVulnerabilities": 13,
            "highRiskApplications": 8
        },
        "recentActivity": [
            {
                "type": "vulnerability",
                "message": "New critical vulnerability found in Customer Portal",
                "timestamp": "2025-11-28T10:30:00Z"
            },
            {
                "type": "compliance",
                "message": "Vendor compliance assessment completed",
                "timestamp": "2025-11-28T09:15:00Z"
            }
        ]
    }


@router.get("/metrics")
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_session)
):
    """Get dashboard metrics"""
    return {
        "vulnerabilityTrends": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "critical": [5, 8, 12, 10, 13, 15],
            "high": [12, 15, 18, 20, 17, 22],
            "medium": [25, 28, 30, 32, 35, 38],
            "low": [40, 42, 45, 48, 50, 52]
        },
        "complianceOverview": {
            "compliant": 75,
            "nonCompliant": 15,
            "pending": 10
        }
    }