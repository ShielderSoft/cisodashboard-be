"""App History API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

from app.db.session import get_session
from app.services.app_history_service import app_history_service
from app.schemas.app_history import AppHistoryResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=AppHistoryResponse)
async def get_app_history(
    year: Optional[int] = Query(None, description="Year to filter data (defaults to current year)"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get complete application vulnerability history data
    
    Returns historical vulnerability data including:
    - Monthly trends (open/closed vulnerabilities by month)
    - Yearly trends (vulnerabilities by severity for last 3 years)
    - Category data (vulnerabilities grouped by application category)
    - Applications list (all applications with vulnerability counts)
    - Total open and closed counts
    
    Args:
        year: Optional year filter (defaults to current year)
        db: Database session
        
    Returns:
        AppHistoryResponse with all history components
    """
    try:
        history_data = await app_history_service.get_app_history(db, year)
        return history_data
    except Exception as e:
        logger.error(f"Error fetching app history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch app history data: {str(e)}"
        )
