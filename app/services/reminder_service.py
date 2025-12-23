"""Reminder service for application reminder management"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from collections import defaultdict

from app.models.models import Application, Vulnerability, User, VulnerabilityStatus, Vendor, VendorComplianceRecord, Exception as ExceptionModel, ComplianceStatus
from app.schemas.reminder import (
    ReminderResponse, OwnerReminderData, ApplicationReminderData,
    OwnerApplicationData, ApplicationInstanceData,
    VulnerabilityCounts, DelayCounts, ReminderStats,
    FrontendReminderResponse, VendorReminderItem, ApplicationReminderItem,
    ExceptionReminderItem, FrontendReminderStats
)

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for handling application reminder operations"""
    
    @staticmethod
    async def get_reminder_data(db: AsyncSession) -> ReminderResponse:
        """
        Get complete reminder data including owner-based and application-based views
        
        Args:
            db: Database session
            
        Returns:
            ReminderResponse with owner data, application data, and stats
        """
        try:
            # Fetch all applications with their vulnerabilities
            stmt = select(Application).where(Application.owner_id.isnot(None))
            result = await db.execute(stmt)
            applications = result.scalars().all()
            
            # Fetch all open vulnerabilities
            vuln_stmt = select(Vulnerability).where(
                Vulnerability.status == VulnerabilityStatus.OPEN
            )
            vuln_result = await db.execute(vuln_stmt)
            vulnerabilities = vuln_result.scalars().all()
            
            # Build vulnerability map by application_id
            vuln_by_app = defaultdict(list)
            for vuln in vulnerabilities:
                if vuln.application_id:
                    vuln_by_app[vuln.application_id].append(vuln)
            
            # Fetch user details for owners
            user_ids = [app.owner_id for app in applications if app.owner_id]
            user_stmt = select(User).where(User.id.in_(user_ids))
            user_result = await db.execute(user_stmt)
            users = {user.id: user for user in user_result.scalars().all()}
            
            # Process data for owner view
            owner_data_dict = {}
            for app in applications:
                if not app.owner_id:
                    continue
                    
                owner = users.get(app.owner_id)
                if not owner:
                    continue
                    
                owner_name = owner.full_name or owner.email
                
                # Get vulnerabilities for this application
                app_vulns = vuln_by_app.get(app.id, [])
                
                # Calculate vulnerability counts and delays
                vuln_counts, delay_counts = ReminderService._calculate_metrics(app_vulns)
                
                # Create owner application data
                owner_app = OwnerApplicationData(
                    id=f"APP-{app.id}",
                    name=app.name,
                    vulnerabilities=vuln_counts,
                    delay=delay_counts,
                    lastReminded=None,  # TODO: Track reminder history
                    owner=owner_name
                )
                
                # Group by owner
                if owner.id not in owner_data_dict:
                    owner_data_dict[owner.id] = {
                        "id": f"OWN-{owner.id}",
                        "name": owner_name,
                        "applications": [],
                        "totalVulnerabilities": 0
                    }
                
                owner_data_dict[owner.id]["applications"].append(owner_app)
                owner_data_dict[owner.id]["totalVulnerabilities"] += vuln_counts.total
            
            # Convert owner data dict to list
            owner_data = [
                OwnerReminderData(
                    id=data["id"],
                    name=data["name"],
                    applicationCount=len(data["applications"]),
                    totalVulnerabilities=data["totalVulnerabilities"],
                    applications=data["applications"]
                )
                for data in owner_data_dict.values()
            ]
            
            # Process data for application view
            app_data_dict = {}
            for app in applications:
                if not app.owner_id:
                    continue
                    
                owner = users.get(app.owner_id)
                if not owner:
                    continue
                    
                owner_name = owner.full_name or owner.email
                
                # Get vulnerabilities for this application
                app_vulns = vuln_by_app.get(app.id, [])
                
                # Calculate vulnerability counts and delays
                vuln_counts, delay_counts = ReminderService._calculate_metrics(app_vulns)
                
                # Create application instance
                app_instance = ApplicationInstanceData(
                    id=f"APP-{app.id}-OWN-{owner.id}",
                    owner=owner_name,
                    vulnerabilities=vuln_counts,
                    delay=delay_counts,
                    lastReminded=None  # TODO: Track reminder history
                )
                
                # Group by application name
                if app.name not in app_data_dict:
                    app_data_dict[app.name] = {
                        "id": f"APPGRP-{app.id}",
                        "name": app.name,
                        "instances": []
                    }
                
                app_data_dict[app.name]["instances"].append(app_instance)
            
            # Convert application data dict to list
            application_data = [
                ApplicationReminderData(
                    id=data["id"],
                    name=data["name"],
                    instances=data["instances"]
                )
                for data in app_data_dict.values()
            ]
            
            # Calculate statistics
            total_owners = len(owner_data)
            total_applications = len(applications)
            total_vulnerabilities = len(vulnerabilities)
            
            stats = ReminderStats(
                owners=total_owners,
                applications=total_applications,
                totalVulnerabilities=total_vulnerabilities
            )
            
            return ReminderResponse(
                ownerData=owner_data,
                applicationData=application_data,
                stats=stats
            )
            
        except Exception as e:
            logger.error(f"Error fetching reminder data: {str(e)}")
            raise
    
    @staticmethod
    def _calculate_metrics(vulnerabilities: List[Vulnerability]) -> tuple[VulnerabilityCounts, DelayCounts]:
        """
        Calculate vulnerability counts and delay metrics
        
        Args:
            vulnerabilities: List of vulnerabilities
            
        Returns:
            Tuple of (VulnerabilityCounts, DelayCounts)
        """
        vuln_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        delay_days = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        # Use timezone-aware datetime to match database datetime fields
        today = datetime.now(timezone.utc)
        
        for vuln in vulnerabilities:
            severity = vuln.severity.lower() if vuln.severity else "low"
            if severity not in vuln_counts:
                severity = "low"
            
            vuln_counts[severity] += 1
            
            # Calculate delay days
            if vuln.discovered_date:
                # Ensure both are datetime objects for comparison
                discovered = vuln.discovered_date
                if isinstance(discovered, date) and not isinstance(discovered, datetime):
                    discovered = datetime.combine(discovered, datetime.min.time(), tzinfo=timezone.utc)
                
                delta = today - discovered
                delay_days[severity].append(delta.days)
        
        # Calculate average or max delays
        delay_counts_dict = {}
        for severity in ["critical", "high", "medium", "low"]:
            if delay_days[severity]:
                delay_counts_dict[severity] = max(delay_days[severity])
            else:
                delay_counts_dict[severity] = 0
        
        total_vulns = sum(vuln_counts.values())
        max_delay = max(delay_counts_dict.values()) if delay_counts_dict else 0
        
        return (
            VulnerabilityCounts(
                critical=vuln_counts["critical"],
                high=vuln_counts["high"],
                medium=vuln_counts["medium"],
                low=vuln_counts["low"],
                total=total_vulns
            ),
            DelayCounts(
                critical=delay_counts_dict["critical"],
                high=delay_counts_dict["high"],
                medium=delay_counts_dict["medium"],
                low=delay_counts_dict["low"],
                max=max_delay
            )
        )
    
    @staticmethod
    async def send_reminder(
        db: AsyncSession,
        application_id: int,
        owner_id: Optional[int] = None
    ) -> Dict:
        """
        Send reminder for an application (placeholder - actual email sending would go here)
        
        Args:
            db: Database session
            application_id: Application ID
            owner_id: Optional owner ID, if None sends to all owners
            
        Returns:
            Dict with success status and message
        """
        try:
            # Fetch application
            stmt = select(Application).where(Application.id == application_id)
            result = await db.execute(stmt)
            application = result.scalar_one_or_none()
            
            if not application:
                return {
                    "success": False,
                    "message": f"Application {application_id} not found"
                }
            
            # TODO: Implement actual reminder sending logic (email, notification, etc.)
            # For now, just log and return success
            
            logger.info(f"Reminder sent for application {application.name} (ID: {application_id})")
            
            return {
                "success": True,
                "message": "Reminder sent successfully",
                "remindedAt": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send reminder: {str(e)}"
            }

    @staticmethod
    async def get_frontend_reminder_data(db: AsyncSession) -> FrontendReminderResponse:
        """
        Get reminder data formatted for the frontend Reminder page
        
        Returns data in three categories:
        - Vendor reminders: Vendors with non-compliant applications
        - Application reminders: Applications with vulnerabilities/delays
        - Exception reminders: Active exceptions requiring attention
        
        Args:
            db: Database session
            
        Returns:
            FrontendReminderResponse with all three reminder categories
        """
        try:
            # Get vendor reminders - vendors with expired or non-compliant records
            vendor_reminders = []
            
            # Query vendors with non-compliant compliance records
            vendor_stmt = select(Vendor).where(Vendor.compliance_status == ComplianceStatus.NON_COMPLIANT)
            vendor_result = await db.execute(vendor_stmt)
            vendors = vendor_result.scalars().all()
            
            for vendor in vendors:
                # Get vendor compliance records to calculate delay
                compliance_stmt = select(VendorComplianceRecord).where(
                    and_(
                        VendorComplianceRecord.vendor_id == vendor.id,
                        VendorComplianceRecord.status == ComplianceStatus.NON_COMPLIANT
                    )
                )
                compliance_result = await db.execute(compliance_stmt)
                compliance_records = compliance_result.scalars().all()
                
                # Calculate delay days (days since last assessment or expiry)
                max_delay = 0
                today = date.today()
                for record in compliance_records:
                    if record.expiry_date and record.expiry_date < today:
                        delay = (today - record.expiry_date).days
                        max_delay = max(max_delay, delay)
                    elif record.assessment_date:
                        # If no expiry, use assessment date
                        delay = (today - record.assessment_date).days
                        max_delay = max(max_delay, delay)
                
                # Count non-compliant "apps" (compliance records)
                non_compliant_count = len(compliance_records)
                
                if non_compliant_count > 0:
                    vendor_reminders.append(VendorReminderItem(
                        id=f"VR-{vendor.id}",
                        vendorName=vendor.name,
                        nonCompliantApps=non_compliant_count,
                        delayDays=max_delay,
                        sentCount=0  # TODO: Track reminder history
                    ))
            
            # Get application reminders - applications with open vulnerabilities
            application_reminders = []
            
            # Query applications with open vulnerabilities
            app_stmt = select(Application).where(Application.owner_id.isnot(None))
            app_result = await db.execute(app_stmt)
            applications = app_result.scalars().all()
            
            # Get all open vulnerabilities
            vuln_stmt = select(Vulnerability).where(Vulnerability.status == VulnerabilityStatus.OPEN)
            vuln_result = await db.execute(vuln_stmt)
            vulnerabilities = vuln_result.scalars().all()
            
            # Group vulnerabilities by application
            vuln_by_app = defaultdict(list)
            for vuln in vulnerabilities:
                if vuln.application_id:
                    vuln_by_app[vuln.application_id].append(vuln)
            
            # Get user details for owners
            user_ids = [app.owner_id for app in applications if app.owner_id]
            if user_ids:
                user_stmt = select(User).where(User.id.in_(user_ids))
                user_result = await db.execute(user_stmt)
                users = {user.id: user for user in user_result.scalars().all()}
            else:
                users = {}
            
            # Process applications with vulnerabilities
            for app in applications:
                if not app.owner_id:
                    continue
                
                app_vulns = vuln_by_app.get(app.id, [])
                if not app_vulns:
                    continue
                
                owner = users.get(app.owner_id)
                if not owner:
                    continue
                
                owner_name = owner.full_name or owner.email
                
                # Calculate max delay from vulnerabilities
                max_delay = 0
                today = datetime.now(timezone.utc)
                for vuln in app_vulns:
                    if vuln.discovered_date:
                        discovered = vuln.discovered_date
                        if isinstance(discovered, date) and not isinstance(discovered, datetime):
                            discovered = datetime.combine(discovered, datetime.min.time(), tzinfo=timezone.utc)
                        delay = (today - discovered).days
                        max_delay = max(max_delay, delay)
                
                application_reminders.append(ApplicationReminderItem(
                    id=f"AR-{app.id}",
                    owner=owner_name,
                    application=app.name,
                    delayDays=max_delay,
                    sentCount=0,  # TODO: Track reminder history
                    applicationId=app.id,
                    ownerId=app.owner_id
                ))
            
            # Get exception reminders - active exceptions
            exception_reminders = []
            
            # Query active exceptions
            exception_stmt = select(ExceptionModel).where(
                ExceptionModel.status.in_(['active', 'pending'])
            )
            exception_result = await db.execute(exception_stmt)
            exceptions = exception_result.scalars().all()
            
            for exc in exceptions:
                # Use exception_name as type and comments/risk_assessment as remark
                exception_type = exc.exception_name or exc.category or "Unknown Exception"
                remark = exc.comments or exc.risk_assessment or "No remarks available"
                
                exception_reminders.append(ExceptionReminderItem(
                    id=f"ER-{exc.id}",
                    exceptionType=exception_type,
                    remark=remark,
                    sentCount=0,  # TODO: Track reminder history
                    exceptionId=exc.id
                ))
            
            # Calculate statistics
            stats = FrontendReminderStats(
                vendors=len(vendor_reminders),
                applications=len(application_reminders),
                exceptions=len(exception_reminders)
            )
            
            return FrontendReminderResponse(
                vendorReminders=vendor_reminders,
                applicationReminders=application_reminders,
                exceptionReminders=exception_reminders,
                stats=stats
            )
            
        except Exception as e:
            logger.error(f"Error fetching frontend reminder data: {str(e)}")
            raise

    @staticmethod
    async def send_vendor_reminder(
        db: AsyncSession,
        vendor_id: int
    ) -> Dict:
        """
        Send reminder for a vendor (placeholder - actual email sending would go here)
        
        Args:
            db: Database session
            vendor_id: Vendor ID
            
        Returns:
            Dict with success status and message
        """
        try:
            # Fetch vendor
            stmt = select(Vendor).where(Vendor.id == vendor_id)
            result = await db.execute(stmt)
            vendor = result.scalar_one_or_none()
            
            if not vendor:
                return {
                    "success": False,
                    "message": f"Vendor {vendor_id} not found",
                    "remindedAt": datetime.now().isoformat()
                }
            
            # TODO: Implement actual reminder sending logic (email, notification, etc.)
            # For now, just log and return success
            
            logger.info(f"Reminder sent for vendor {vendor.name} (ID: {vendor_id})")
            
            return {
                "success": True,
                "message": f"Vendor reminder sent successfully to {vendor.name}",
                "remindedAt": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending vendor reminder: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send vendor reminder: {str(e)}",
                "remindedAt": datetime.now().isoformat()
            }

    @staticmethod
    async def send_exception_reminder(
        db: AsyncSession,
        exception_id: int
    ) -> Dict:
        """
        Send reminder for an exception (placeholder - actual email sending would go here)
        
        Args:
            db: Database session
            exception_id: Exception ID
            
        Returns:
            Dict with success status and message
        """
        try:
            # Fetch exception
            stmt = select(ExceptionModel).where(ExceptionModel.id == exception_id)
            result = await db.execute(stmt)
            exception = result.scalar_one_or_none()
            
            if not exception:
                return {
                    "success": False,
                    "message": f"Exception {exception_id} not found",
                    "remindedAt": datetime.now().isoformat()
                }
            
            # TODO: Implement actual reminder sending logic (email, notification, etc.)
            # For now, just log and return success
            
            logger.info(f"Reminder sent for exception {exception.exception_name} (ID: {exception_id})")
            
            return {
                "success": True,
                "message": f"Exception reminder sent successfully for {exception.exception_name}",
                "remindedAt": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending exception reminder: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send exception reminder: {str(e)}",
                "remindedAt": datetime.now().isoformat()
            }
