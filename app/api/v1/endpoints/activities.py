"""
Activity Log API Endpoints
RESTful API for activity logs and general updates
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.db.session import get_session
from app.services.activity_service import ActivityLogService
from app.schemas.activity_log import (
    ActivityLogCreate,
    ActivityLogUpdate,
    ActivityLogResponse,
    ActivityLogListResponse,
    ActivityStatistics,
    ActivityFilter,
    ActivityTypeEnum,
    ActivityPriorityEnum
)

router = APIRouter()


@router.get("/activities", response_model=ActivityLogListResponse)
async def get_activities(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    activity_type: Optional[List[ActivityTypeEnum]] = Query(None, description="Filter by activity types"),
    priority: Optional[List[ActivityPriorityEnum]] = Query(None, description="Filter by priority"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (application, vendor, etc.)"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get paginated list of activity logs with optional filters.
    
    This endpoint supports comprehensive filtering:
    - **days**: How far back to look (default: 7 days)
    - **activity_type**: Filter by one or more activity types
    - **priority**: Filter by priority level
    - **entity_type**: Filter by entity type (application, vendor, vulnerability, etc.)
    - **entity_id**: Get activities for a specific entity
    - **user_id**: Get activities by a specific user
    - **is_read**: Filter by read/unread status
    - **tags**: Filter by tags
    
    Returns paginated results with metadata.
    """
    try:
        filters = ActivityFilter(
            activity_type=activity_type,
            priority=priority,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            is_read=is_read,
            days=days,
            tags=tags
        )
        
        result = await ActivityLogService.get_activities(
            db=db,
            page=page,
            size=size,
            filters=filters
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activities: {str(e)}"
        )


@router.get("/activities/{activity_id}", response_model=ActivityLogResponse)
async def get_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Get a single activity by ID"""
    try:
        activity = await ActivityLogService.get_activity_by_id(db, activity_id)
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found"
            )
        
        return ActivityLogResponse.from_orm(activity)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity: {str(e)}"
        )


@router.post("/activities", response_model=ActivityLogResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityLogCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new activity log entry.
    
    This endpoint is typically called programmatically by other services
    when significant events occur in the system.
    """
    try:
        activity = await ActivityLogService.create_activity(
            db=db,
            activity_data=activity_data
        )
        
        return ActivityLogResponse.from_orm(activity)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )


@router.patch("/activities/{activity_id}", response_model=ActivityLogResponse)
async def update_activity(
    activity_id: int,
    update_data: ActivityLogUpdate,
    db: AsyncSession = Depends(get_session)
):
    """
    Update an activity (limited fields: is_read, status).
    
    Use this to mark activities as read or archive them.
    """
    try:
        activity = await ActivityLogService.update_activity(
            db=db,
            activity_id=activity_id,
            update_data=update_data
        )
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found"
            )
        
        return ActivityLogResponse.from_orm(activity)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update activity: {str(e)}"
        )


@router.post("/activities/mark-read")
async def mark_activities_as_read(
    activity_ids: List[int],
    db: AsyncSession = Depends(get_session)
):
    """
    Mark multiple activities as read.
    
    Useful for bulk operations when user views the updates panel.
    """
    try:
        count = await ActivityLogService.mark_as_read(db, activity_ids)
        
        return {
            "success": True,
            "message": f"Marked {count} activities as read",
            "count": count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark activities as read: {str(e)}"
        )


@router.get("/activities-statistics", response_model=ActivityStatistics)
async def get_activity_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days for statistics"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get activity statistics.
    
    Returns:
    - Total activities
    - Unread count
    - Breakdown by priority
    - Breakdown by type
    - Recent activity counts
    """
    try:
        stats = await ActivityLogService.get_statistics(db, days)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


@router.post("/activities/archive-old")
async def archive_old_activities(
    days: int = Query(90, ge=30, le=365, description="Archive activities older than this many days"),
    db: AsyncSession = Depends(get_session)
):
    """
    Archive old activities (admin operation).
    
    This helps maintain performance by moving old activities to archived status.
    Archived activities are not shown in normal queries.
    """
    try:
        count = await ActivityLogService.archive_old_activities(db, days)
        
        return {
            "success": True,
            "message": f"Archived {count} activities older than {days} days",
            "count": count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive activities: {str(e)}"
        )


@router.get("/activities/by-entity/{entity_type}/{entity_id}", response_model=ActivityLogListResponse)
async def get_activities_by_entity(
    entity_type: str,
    entity_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session)
):
    """
    Get all activities related to a specific entity.
    
    Useful for showing activity history on detail pages:
    - Application detail page: show all activities for that application
    - Vendor detail page: show all activities for that vendor
    - etc.
    """
    try:
        filters = ActivityFilter(
            entity_type=entity_type,
            entity_id=entity_id,
            days=365  # Show all activities for the entity
        )
        
        result = await ActivityLogService.get_activities(
            db=db,
            page=page,
            size=size,
            filters=filters
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch entity activities: {str(e)}"
        )
