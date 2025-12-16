"""Reminder service for application reminder management"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from collections import defaultdict

from app.models.models import Application, Vulnerability, User, VulnerabilityStatus
from app.schemas.reminder import (
    ReminderResponse, OwnerReminderData, ApplicationReminderData,
    OwnerApplicationData, ApplicationInstanceData,
    VulnerabilityCounts, DelayCounts, ReminderStats
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
