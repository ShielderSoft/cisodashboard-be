"""
API endpoints for vendor expiry notifications
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_session
from app.services.vendor_expiry_notification import vendor_expiry_notification_service
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class ExpiryCheckResponse(BaseModel):
    """Response model for expiry check"""
    success: bool
    message: str
    total_checked: int
    emails_sent: int
    emails_failed: int
    vendors_without_email: int
    details: list


class TestNotificationResponse(BaseModel):
    """Response model for test notification"""
    success: bool
    message: str
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None
    contact_email: Optional[str] = None
    expiry_date: Optional[str] = None
    days_until_expiry: Optional[int] = None
    error: Optional[str] = None


@router.post("/check-expiring-vendors", response_model=ExpiryCheckResponse)
async def check_expiring_vendors(
    days_before: int = Query(8, ge=1, le=90, description="Number of days before expiry to check"),
    db: AsyncSession = Depends(get_session)
):
    """
    Check for vendors with certificates expiring soon and send email notifications
    
    This endpoint checks all vendors whose certificates expire within the specified
    number of days and sends email notifications to their contact emails.
    
    Args:
        days_before: Number of days before expiry to check (default: 8, range: 1-90)
        db: Database session
    
    Returns:
        Statistics about notifications sent
    """
    try:
        logger.info(f"🔔 Manual trigger: Checking vendors expiring within {days_before} days")
        
        # Run the expiry check
        stats = await vendor_expiry_notification_service.check_and_notify_expiring_vendors(
            db=db,
            days_before=days_before
        )
        
        return ExpiryCheckResponse(
            success=True,
            message=f"Expiry check completed. Sent {stats['emails_sent']} notifications.",
            total_checked=stats["total_checked"],
            emails_sent=stats["emails_sent"],
            emails_failed=stats["emails_failed"],
            vendors_without_email=stats["vendors_without_email"],
            details=stats["details"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error during expiry check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check expiring vendors: {str(e)}"
        )


@router.post("/test-notification/{vendor_id}", response_model=TestNotificationResponse)
async def send_test_notification(
    vendor_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Send a test expiry notification email to a specific vendor
    
    This endpoint sends a test notification to the specified vendor's contact email
    regardless of the actual expiry date. Useful for testing the email system.
    
    Args:
        vendor_id: ID of the vendor to send test notification
        db: Database session
    
    Returns:
        Result of the test notification
    """
    try:
        logger.info(f"📧 Sending test notification for vendor ID: {vendor_id}")
        
        result = await vendor_expiry_notification_service.send_test_notification(
            db=db,
            vendor_id=vendor_id
        )
        
        if result["success"]:
            return TestNotificationResponse(
                success=True,
                message=f"Test notification sent successfully to {result['contact_email']}",
                vendor_id=result.get("vendor_id"),
                vendor_name=result.get("vendor_name"),
                contact_email=result.get("contact_email"),
                expiry_date=result.get("expiry_date"),
                days_until_expiry=result.get("days_until_expiry")
            )
        else:
            return TestNotificationResponse(
                success=False,
                message="Failed to send test notification",
                error=result.get("error"),
                vendor_id=result.get("vendor_id"),
                vendor_name=result.get("vendor_name")
            )
            
    except Exception as e:
        logger.error(f"❌ Error sending test notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )


@router.get("/expiring-vendors-list")
async def get_expiring_vendors_list(
    days_before: int = Query(8, ge=1, le=90, description="Number of days before expiry"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get list of vendors with certificates expiring within specified days
    
    This endpoint returns a list of vendors without sending any notifications.
    Useful for previewing which vendors would receive notifications.
    
    Args:
        days_before: Number of days before expiry to check (default: 8)
        db: Database session
    
    Returns:
        List of expiring vendors
    """
    try:
        from datetime import date, timedelta
        from sqlalchemy import select, and_
        from app.models.models import Vendor
        
        today = date.today()
        target_date = today + timedelta(days=days_before)
        
        # Query vendors
        query = select(Vendor).where(
            and_(
                Vendor.certificate_expiry_date.isnot(None),
                Vendor.certificate_expiry_date <= target_date
            )
        ).order_by(Vendor.certificate_expiry_date)
        
        result = await db.execute(query)
        vendors = result.scalars().all()
        
        vendor_list = []
        for vendor in vendors:
            days_until = (vendor.certificate_expiry_date - today).days
            vendor_list.append({
                "id": vendor.id,
                "name": vendor.name,
                "category": vendor.category,
                "contact_email": vendor.contact_email,
                "certificate_expiry_date": str(vendor.certificate_expiry_date),
                "days_until_expiry": days_until,
                "status": "expired" if days_until < 0 else "expiring_soon",
                "has_email": bool(vendor.contact_email)
            })
        
        return {
            "success": True,
            "total_vendors": len(vendor_list),
            "days_before": days_before,
            "check_date": str(today),
            "target_date": str(target_date),
            "vendors": vendor_list
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting expiring vendors list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get expiring vendors: {str(e)}"
        )
