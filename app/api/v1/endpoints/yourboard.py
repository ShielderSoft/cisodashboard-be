"""
YourBoard Dashboard Endpoint
Provides real-time metrics for CISO dashboard
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from datetime import datetime, timedelta
from typing import Dict, Any

from app.db.session import get_db
from app.models.models import (
    Application,
    Vulnerability,
    Vendor,
    Exception as ExceptionModel
)
from app.services.audit_service import audit_service

router = APIRouter()


@router.get("/yourboard-metrics", response_model=Dict[str, Any])
async def get_yourboard_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time metrics for YourBoard dashboard with monthly trends
    
    Returns:
    - App Track: Total number of applications
    - Infra Track: Total number of vulnerabilities
    - Audit Track: Total number of non-compliant vendors
    - Exceptions: Total number of exception cases
    
    Each metric includes trend percentage compared to last month
    """
    
    # Get current date and previous month for trend calculation
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year
    
    # Calculate previous month
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year
    
    try:
        # ============= APP TRACK: Total Applications =============
        # Current month applications
        app_current_query = select(func.count(Application.id)).where(
            and_(
                extract('month', Application.created_at) == current_month,
                extract('year', Application.created_at) == current_year
            )
        )
        app_current_result = await db.execute(app_current_query)
        app_current_count = app_current_result.scalar() or 0
        
        # Previous month applications
        app_prev_query = select(func.count(Application.id)).where(
            and_(
                extract('month', Application.created_at) == prev_month,
                extract('year', Application.created_at) == prev_year
            )
        )
        app_prev_result = await db.execute(app_prev_query)
        app_prev_count = app_prev_result.scalar() or 0
        
        # Total applications count (for display)
        app_total_query = select(func.count(Application.id))
        app_total_result = await db.execute(app_total_query)
        app_total_count = app_total_result.scalar() or 0
        
        # Calculate trend
        app_trend = calculate_trend(app_current_count, app_prev_count)
        app_direction = 'up' if app_current_count > app_prev_count else 'down'
        
        
        # ============= INFRA TRACK: Total Vulnerabilities =============
        # Current month vulnerabilities
        vuln_current_query = select(func.count(Vulnerability.id)).where(
            and_(
                extract('month', Vulnerability.created_at) == current_month,
                extract('year', Vulnerability.created_at) == current_year
            )
        )
        vuln_current_result = await db.execute(vuln_current_query)
        vuln_current_count = vuln_current_result.scalar() or 0
        
        # Previous month vulnerabilities
        vuln_prev_query = select(func.count(Vulnerability.id)).where(
            and_(
                extract('month', Vulnerability.created_at) == prev_month,
                extract('year', Vulnerability.created_at) == prev_year
            )
        )
        vuln_prev_result = await db.execute(vuln_prev_query)
        vuln_prev_count = vuln_prev_result.scalar() or 0
        
        # Total vulnerabilities (for display)
        vuln_total_query = select(func.count(Vulnerability.id))
        vuln_total_result = await db.execute(vuln_total_query)
        vuln_total_count = vuln_total_result.scalar() or 0
        
        # Calculate trend
        vuln_trend = calculate_trend(vuln_current_count, vuln_prev_count)
        vuln_direction = 'down' if vuln_current_count < vuln_prev_count else 'up'
        
        
        # ============= AUDIT TRACK: Non-Compliant Vendors =============
        # Use audit_service to get consistent certificate-based compliance data
        audit_stats = await audit_service.get_statistics(db)
        
        vendor_total_count = audit_stats.non_compliant
        
        # Use the non_compliant_trend from audit_stats (represents percentage of total vendors)
        vendor_trend = int(audit_stats.non_compliant_trend) if audit_stats.non_compliant_trend else 0
        
        # Direction: 'up' is bad (more non-compliant), 'down' is good (fewer non-compliant)
        vendor_direction = 'up' if vendor_total_count > 0 else 'down'
        
        
        # ============= EXCEPTIONS: Total Exception Cases =============
        # Current month exceptions
        exc_current_query = select(func.count(ExceptionModel.id)).where(
            and_(
                extract('month', ExceptionModel.created_at) == current_month,
                extract('year', ExceptionModel.created_at) == current_year
            )
        )
        exc_current_result = await db.execute(exc_current_query)
        exc_current_count = exc_current_result.scalar() or 0
        
        # Previous month exceptions
        exc_prev_query = select(func.count(ExceptionModel.id)).where(
            and_(
                extract('month', ExceptionModel.created_at) == prev_month,
                extract('year', ExceptionModel.created_at) == prev_year
            )
        )
        exc_prev_result = await db.execute(exc_prev_query)
        exc_prev_count = exc_prev_result.scalar() or 0
        
        # Total exceptions (for display)
        exc_total_query = select(func.count(ExceptionModel.id))
        exc_total_result = await db.execute(exc_total_query)
        exc_total_count = exc_total_result.scalar() or 0
        
        # Calculate trend
        exc_trend = calculate_trend(exc_current_count, exc_prev_count)
        exc_direction = 'up' if exc_current_count > exc_prev_count else 'down'
        
        
        # ============= BUILD RESPONSE =============
        metrics = [
            {
                "title": "App Track",
                "count": app_total_count,
                "unit": "apps",
                "trend": app_trend,
                "trendDirection": app_direction,
                "trendPeriod": "This month"
            },
            {
                "title": "Infra Track",
                "count": vuln_total_count,
                "unit": "vuln",
                "trend": vuln_trend,
                "trendDirection": vuln_direction,
                "trendPeriod": "This month"
            },
            {
                "title": "Audit Track",
                "count": vendor_total_count,
                "unit": "NC",
                "trend": vendor_trend,
                "trendDirection": vendor_direction,
                "trendPeriod": "This month"
            },
            {
                "title": "Exceptions",
                "count": exc_total_count,
                "unit": "cases",
                "trend": exc_trend,
                "trendDirection": exc_direction,
                "trendPeriod": "This month"
            }
        ]
        
        return {
            "success": True,
            "metrics": metrics,
            "lastUpdated": now.strftime('%Y-%m-%d %H:%M:%S'),
            "currentMonth": now.strftime('%B %Y'),
            "metadata": {
                "appTrack": {
                    "currentMonth": app_current_count,
                    "previousMonth": app_prev_count,
                    "total": app_total_count
                },
                "infraTrack": {
                    "currentMonth": vuln_current_count,
                    "previousMonth": vuln_prev_count,
                    "total": vuln_total_count
                },
                "auditTrack": {
                    "currentMonth": vendor_total_count,
                    "previousMonth": 0,  # Historical tracking not yet implemented
                    "total": vendor_total_count,
                    "compliant": audit_stats.compliant,
                    "non_compliant": audit_stats.non_compliant,
                    "exceptions": audit_stats.exceptions
                },
                "exceptions": {
                    "currentMonth": exc_current_count,
                    "previousMonth": exc_prev_count,
                    "total": exc_total_count
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching yourboard metrics: {str(e)}"
        )


def calculate_trend(current: int, previous: int) -> int:
    """
    Calculate percentage trend between current and previous values
    Returns absolute percentage change
    """
    if previous == 0:
        # If previous is 0, return 100% if current > 0, else 0%
        return 100 if current > 0 else 0
    
    change = ((current - previous) / previous) * 100
    return abs(int(change))
