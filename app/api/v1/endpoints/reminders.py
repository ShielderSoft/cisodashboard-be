"""Application Reminder API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_session
from app.services.reminder_service import ReminderService
from app.schemas.reminder import (
    ReminderResponse,
    SendReminderRequest,
    SendReminderResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ReminderResponse)
async def get_reminders(
    db: AsyncSession = Depends(get_session)
):
    """
    Get complete reminder data including owner-based and application-based views
    
    Returns:
        ReminderResponse with owner data, application data, and statistics
    """
    try:
        reminder_data = await ReminderService.get_reminder_data(db)
        return reminder_data
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reminder data: {str(e)}"
        )


@router.post("/send", response_model=SendReminderResponse)
async def send_reminder(
    request: SendReminderRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Send a reminder for an application
    
    Args:
        request: SendReminderRequest with application_id and optional owner_id
        db: Database session
        
    Returns:
        SendReminderResponse with success status and timestamp
    """
    try:
        result = await ReminderService.send_reminder(
            db=db,
            application_id=request.applicationId,
            owner_id=request.ownerId
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return SendReminderResponse(
            success=result["success"],
            message=result["message"],
            remindedAt=result["remindedAt"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reminder: {str(e)}"
        )
