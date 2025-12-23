"""Application Reminder API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_session
from app.services.reminder_service import ReminderService
from app.schemas.reminder import (
    ReminderResponse,
    SendReminderRequest,
    SendReminderResponse,
    FrontendReminderResponse
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


@router.get("/frontend", response_model=FrontendReminderResponse)
async def get_frontend_reminders(
    db: AsyncSession = Depends(get_session)
):
    """
    Get reminder data formatted for the frontend Reminder page
    
    Returns vendor reminders, application reminders, and exception reminders
    with statistics for each category.
    
    Returns:
        FrontendReminderResponse with vendorReminders, applicationReminders, 
        exceptionReminders, and stats
    """
    try:
        reminder_data = await ReminderService.get_frontend_reminder_data(db)
        return reminder_data
    except Exception as e:
        logger.error(f"Error fetching frontend reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch frontend reminder data: {str(e)}"
        )


@router.post("/send", response_model=SendReminderResponse)
async def send_reminder(
    request: SendReminderRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Send a reminder for an application, vendor, or exception
    
    Args:
        request: SendReminderRequest with different options:
            - applicationId + ownerId: Send application reminder
            - targetType + targetId: Generic reminder (vendor, exception, etc.)
            - vendorId: Send vendor reminder
            - exceptionId: Send exception reminder
        db: Database session
        
    Returns:
        SendReminderResponse with success status and timestamp
    """
    try:
        # Determine reminder type and call appropriate service method
        if request.targetType == 'exception' or request.exceptionId:
            exception_id = request.targetId if request.targetType == 'exception' else request.exceptionId
            result = await ReminderService.send_exception_reminder(db=db, exception_id=exception_id)
        elif request.targetType == 'vendor' or request.vendorId:
            vendor_id = request.targetId if request.targetType == 'vendor' else request.vendorId
            result = await ReminderService.send_vendor_reminder(db=db, vendor_id=vendor_id)
        elif request.applicationId:
            result = await ReminderService.send_reminder(
                db=db,
                application_id=request.applicationId,
                owner_id=request.ownerId
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reminder request: Must specify applicationId, vendorId, exceptionId, or targetType+targetId"
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
