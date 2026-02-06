"""
Vendor expiry notification service
Checks for vendors with expiring certificates and sends email notifications
"""
import logging
from datetime import date, timedelta
from typing import List, Dict
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Vendor
from app.core.email import email_service

logger = logging.getLogger(__name__)


class VendorExpiryNotificationService:
    """Service to check and notify vendors about certificate expiry"""
    
    def __init__(self, days_before_expiry: int = 8):
        """
        Initialize the service
        
        Args:
            days_before_expiry: Number of days before expiry to send notification (default: 8)
        """
        self.days_before_expiry = days_before_expiry
        self.email_service = email_service
    
    async def check_and_notify_expiring_vendors(
        self,
        db: AsyncSession,
        days_before: int = None
    ) -> Dict[str, any]:
        """
        Check for vendors with certificates expiring soon and send notifications
        
        Args:
            db: Database session
            days_before: Override the default days before expiry (optional)
        
        Returns:
            Dict with statistics about notifications sent
        """
        days = days_before if days_before is not None else self.days_before_expiry
        
        logger.info(f"🔍 Checking for vendors with certificates expiring within {days} days...")
        
        # Get vendors with expiring certificates
        expiring_vendors = await self._get_expiring_vendors(db, days)
        
        stats = {
            "total_checked": len(expiring_vendors),
            "emails_sent": 0,
            "emails_failed": 0,
            "vendors_without_email": 0,
            "details": []
        }
        
        # Send notifications
        for vendor in expiring_vendors:
            vendor_info = {
                "id": vendor.id,
                "name": vendor.name,
                "category": vendor.category,
                "expiry_date": str(vendor.certificate_expiry_date),
                "contact_email": vendor.contact_email,
                "days_until_expiry": (vendor.certificate_expiry_date - date.today()).days
            }
            
            # Check if vendor has contact email
            if not vendor.contact_email:
                logger.warning(f"⚠️ Vendor '{vendor.name}' (ID: {vendor.id}) has no contact email")
                stats["vendors_without_email"] += 1
                vendor_info["status"] = "no_email"
                stats["details"].append(vendor_info)
                continue
            
            # Calculate days until expiry
            days_until_expiry = (vendor.certificate_expiry_date - date.today()).days
            
            # Send email notification
            try:
                success = self.email_service.send_vendor_expiry_notification(
                    vendor_name=vendor.name,
                    vendor_category=vendor.category or "N/A",
                    expiry_date=vendor.certificate_expiry_date,
                    to_email=vendor.contact_email,
                    days_until_expiry=days_until_expiry,
                    vendor_id=vendor.id
                )
                
                if success:
                    stats["emails_sent"] += 1
                    vendor_info["status"] = "sent"
                    logger.info(f"✅ Notification sent to {vendor.name} ({vendor.contact_email})")
                else:
                    stats["emails_failed"] += 1
                    vendor_info["status"] = "failed"
                    logger.error(f"❌ Failed to send notification to {vendor.name}")
                
            except Exception as e:
                stats["emails_failed"] += 1
                vendor_info["status"] = "error"
                vendor_info["error"] = str(e)
                logger.error(f"❌ Error sending notification to {vendor.name}: {str(e)}")
            
            stats["details"].append(vendor_info)
        
        # Log summary
        logger.info(f"""
📊 Vendor Expiry Notification Summary:
   - Total vendors checked: {stats['total_checked']}
   - Emails sent successfully: {stats['emails_sent']}
   - Emails failed: {stats['emails_failed']}
   - Vendors without email: {stats['vendors_without_email']}
        """)
        
        return stats
    
    async def _get_expiring_vendors(
        self,
        db: AsyncSession,
        days_before: int
    ) -> List[Vendor]:
        """
        Get vendors with certificates expiring within specified days
        
        Args:
            db: Database session
            days_before: Number of days before expiry
        
        Returns:
            List of vendors with expiring certificates
        """
        today = date.today()
        target_date = today + timedelta(days=days_before)
        
        # Query vendors with certificate_expiry_date within the range
        # Include expired and expiring soon certificates
        query = select(Vendor).where(
            and_(
                Vendor.certificate_expiry_date.isnot(None),
                Vendor.certificate_expiry_date <= target_date
            )
        ).order_by(Vendor.certificate_expiry_date)
        
        result = await db.execute(query)
        vendors = result.scalars().all()
        
        logger.info(f"📋 Found {len(vendors)} vendors with certificates expiring within {days_before} days")
        
        return vendors
    
    async def send_test_notification(
        self,
        db: AsyncSession,
        vendor_id: int
    ) -> Dict[str, any]:
        """
        Send a test notification for a specific vendor
        
        Args:
            db: Database session
            vendor_id: ID of the vendor to send test notification
        
        Returns:
            Dict with result of test notification
        """
        # Get vendor
        query = select(Vendor).where(Vendor.id == vendor_id)
        result = await db.execute(query)
        vendor = result.scalar_one_or_none()
        
        if not vendor:
            return {
                "success": False,
                "error": f"Vendor with ID {vendor_id} not found"
            }
        
        if not vendor.contact_email:
            return {
                "success": False,
                "error": f"Vendor '{vendor.name}' has no contact email"
            }
        
        if not vendor.certificate_expiry_date:
            return {
                "success": False,
                "error": f"Vendor '{vendor.name}' has no certificate expiry date"
            }
        
        # Calculate days until expiry
        days_until_expiry = (vendor.certificate_expiry_date - date.today()).days
        
        # Send notification
        try:
            success = self.email_service.send_vendor_expiry_notification(
                vendor_name=vendor.name,
                vendor_category=vendor.category or "N/A",
                expiry_date=vendor.certificate_expiry_date,
                to_email=vendor.contact_email,
                days_until_expiry=days_until_expiry,
                vendor_id=vendor.id
            )
            
            return {
                "success": success,
                "vendor_id": vendor.id,
                "vendor_name": vendor.name,
                "contact_email": vendor.contact_email,
                "expiry_date": str(vendor.certificate_expiry_date),
                "days_until_expiry": days_until_expiry
            }
            
        except Exception as e:
            logger.error(f"❌ Error sending test notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "vendor_id": vendor.id,
                "vendor_name": vendor.name
            }


# Create singleton instance
vendor_expiry_notification_service = VendorExpiryNotificationService()
