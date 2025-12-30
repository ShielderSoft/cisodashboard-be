"""
Activity Log Service
Business logic for creating and managing activity logs
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from app.models.models import ActivityLog, ActivityType, ActivityPriority, User
from app.schemas.activity_log import (
    ActivityLogCreate,
    ActivityLogUpdate,
    ActivityLogResponse,
    ActivityLogListResponse,
    ActivityStatistics,
    ActivityFilter
)

logger = logging.getLogger(__name__)


class ActivityLogService:
    """
    Service for managing activity logs with efficient querying and creation.
    
    Design principles:
    - Fire-and-forget: Activity creation should never block main operations
    - Batching: Support bulk creation for performance
    - Caching: Cache user names to reduce joins
    - Archiving: Old activities can be archived for performance
    """
    
    @staticmethod
    async def create_activity(
        db: AsyncSession,
        activity_data: ActivityLogCreate,
        auto_commit: bool = True
    ) -> ActivityLog:
        """
        Create a new activity log entry.
        
        Args:
            db: Database session
            activity_data: Activity data
            auto_commit: Whether to commit immediately (default True)
            
        Returns:
            Created activity log entry
        """
        try:
            # If user_id provided but no user_name, fetch it
            if activity_data.user_id and not activity_data.user_name:
                user = await db.get(User, activity_data.user_id)
                if user:
                    activity_data.user_name = user.full_name or user.email
            
            # Create activity
            activity = ActivityLog(
                activity_type=activity_data.activity_type,
                priority=activity_data.priority,
                title=activity_data.title,
                description=activity_data.description,
                user_id=activity_data.user_id,
                user_name=activity_data.user_name,
                entity_type=activity_data.entity_type,
                entity_id=activity_data.entity_id,
                entity_name=activity_data.entity_name,
                extra_data=activity_data.extra_data,
                tags=activity_data.tags,
                status="active",
                is_read=False
            )
            
            db.add(activity)
            
            if auto_commit:
                await db.commit()
                await db.refresh(activity)
            
            logger.info(f"Activity created: {activity.activity_type} - {activity.title}")
            return activity
            
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            if auto_commit:
                await db.rollback()
            raise
    
    @staticmethod
    async def create_bulk_activities(
        db: AsyncSession,
        activities_data: List[ActivityLogCreate]
    ) -> List[ActivityLog]:
        """
        Create multiple activity log entries in bulk for performance.
        
        Args:
            db: Database session
            activities_data: List of activity data
            
        Returns:
            List of created activities
        """
        try:
            activities = []
            for activity_data in activities_data:
                activity = ActivityLog(
                    activity_type=activity_data.activity_type,
                    priority=activity_data.priority,
                    title=activity_data.title,
                    description=activity_data.description,
                    user_id=activity_data.user_id,
                    user_name=activity_data.user_name,
                    entity_type=activity_data.entity_type,
                    entity_id=activity_data.entity_id,
                    entity_name=activity_data.entity_name,
                    extra_data=activity_data.extra_data,
                    tags=activity_data.tags,
                    status="active",
                    is_read=False
                )
                activities.append(activity)
            
            db.add_all(activities)
            await db.commit()
            
            logger.info(f"Bulk created {len(activities)} activities")
            return activities
            
        except Exception as e:
            logger.error(f"Error bulk creating activities: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def get_activities(
        db: AsyncSession,
        page: int = 1,
        size: int = 50,
        filters: Optional[ActivityFilter] = None
    ) -> ActivityLogListResponse:
        """
        Get paginated activity logs with filters.
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            size: Number of items per page
            filters: Optional filters
            
        Returns:
            Paginated list of activities
        """
        try:
            # Build query
            query = select(ActivityLog)
            
            # Apply filters
            conditions = []
            
            if filters:
                # Date filter (default last 7 days)
                if filters.days:
                    cutoff_date = datetime.utcnow() - timedelta(days=filters.days)
                    conditions.append(ActivityLog.created_at >= cutoff_date)
                
                # Activity type filter
                if filters.activity_type:
                    conditions.append(ActivityLog.activity_type.in_(filters.activity_type))
                
                # Priority filter
                if filters.priority:
                    conditions.append(ActivityLog.priority.in_(filters.priority))
                
                # Entity filters
                if filters.entity_type:
                    conditions.append(ActivityLog.entity_type == filters.entity_type)
                
                if filters.entity_id:
                    conditions.append(ActivityLog.entity_id == filters.entity_id)
                
                # User filter
                if filters.user_id:
                    conditions.append(ActivityLog.user_id == filters.user_id)
                
                # Read status filter
                if filters.is_read is not None:
                    conditions.append(ActivityLog.is_read == filters.is_read)
                
                # Tags filter
                if filters.tags:
                    # JSON array contains any of the specified tags
                    tag_conditions = [
                        ActivityLog.tags.contains([tag]) for tag in filters.tags
                    ]
                    conditions.append(or_(*tag_conditions))
            
            # Apply conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Always show active items only
            query = query.where(ActivityLog.status == "active")
            
            # Order by most recent first
            query = query.order_by(desc(ActivityLog.created_at))
            
            # Count total
            count_query = select(func.count()).select_from(ActivityLog)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_query = count_query.where(ActivityLog.status == "active")
            
            result = await db.execute(count_query)
            total = result.scalar_one()
            
            # Paginate
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)
            
            # Execute
            result = await db.execute(query)
            activities = result.scalars().all()
            
            # Calculate pages
            pages = (total + size - 1) // size
            
            return ActivityLogListResponse(
                items=[ActivityLogResponse.from_orm(activity) for activity in activities],
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error getting activities: {e}")
            raise
    
    @staticmethod
    async def get_activity_by_id(
        db: AsyncSession,
        activity_id: int
    ) -> Optional[ActivityLog]:
        """Get a single activity by ID"""
        try:
            result = await db.execute(
                select(ActivityLog).where(ActivityLog.id == activity_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting activity {activity_id}: {e}")
            raise
    
    @staticmethod
    async def update_activity(
        db: AsyncSession,
        activity_id: int,
        update_data: ActivityLogUpdate
    ) -> Optional[ActivityLog]:
        """Update activity (limited fields like is_read, status)"""
        try:
            activity = await ActivityLogService.get_activity_by_id(db, activity_id)
            
            if not activity:
                return None
            
            # Update only allowed fields
            if update_data.is_read is not None:
                activity.is_read = update_data.is_read
            
            if update_data.status is not None:
                activity.status = update_data.status
            
            await db.commit()
            await db.refresh(activity)
            
            return activity
            
        except Exception as e:
            logger.error(f"Error updating activity {activity_id}: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        activity_ids: List[int]
    ) -> int:
        """Mark multiple activities as read"""
        try:
            from sqlalchemy import update
            
            stmt = (
                update(ActivityLog)
                .where(ActivityLog.id.in_(activity_ids))
                .values(is_read=True)
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            return result.rowcount
            
        except Exception as e:
            logger.error(f"Error marking activities as read: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def get_statistics(
        db: AsyncSession,
        days: int = 7
    ) -> ActivityStatistics:
        """Get activity statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cutoff_24h = datetime.utcnow() - timedelta(hours=24)
            
            # Total activities
            total_result = await db.execute(
                select(func.count())
                .select_from(ActivityLog)
                .where(ActivityLog.created_at >= cutoff_date)
                .where(ActivityLog.status == "active")
            )
            total_activities = total_result.scalar_one()
            
            # Unread count
            unread_result = await db.execute(
                select(func.count())
                .select_from(ActivityLog)
                .where(ActivityLog.is_read == False)
                .where(ActivityLog.status == "active")
            )
            unread_count = unread_result.scalar_one()
            
            # By priority
            priority_result = await db.execute(
                select(
                    ActivityLog.priority,
                    func.count(ActivityLog.id)
                )
                .where(ActivityLog.created_at >= cutoff_date)
                .where(ActivityLog.status == "active")
                .group_by(ActivityLog.priority)
            )
            by_priority = {str(row[0].value): row[1] for row in priority_result.all()}
            
            # By type (top 10)
            type_result = await db.execute(
                select(
                    ActivityLog.activity_type,
                    func.count(ActivityLog.id)
                )
                .where(ActivityLog.created_at >= cutoff_date)
                .where(ActivityLog.status == "active")
                .group_by(ActivityLog.activity_type)
                .order_by(desc(func.count(ActivityLog.id)))
                .limit(10)
            )
            by_type = {str(row[0].value): row[1] for row in type_result.all()}
            
            # Recent 24h
            recent_24h_result = await db.execute(
                select(func.count())
                .select_from(ActivityLog)
                .where(ActivityLog.created_at >= cutoff_24h)
                .where(ActivityLog.status == "active")
            )
            recent_24h = recent_24h_result.scalar_one()
            
            return ActivityStatistics(
                total_activities=total_activities,
                unread_count=unread_count,
                by_priority=by_priority,
                by_type=by_type,
                recent_24h=recent_24h,
                recent_7d=total_activities
            )
            
        except Exception as e:
            logger.error(f"Error getting activity statistics: {e}")
            raise
    
    @staticmethod
    async def archive_old_activities(
        db: AsyncSession,
        days: int = 90
    ) -> int:
        """Archive activities older than specified days"""
        try:
            from sqlalchemy import update
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = (
                update(ActivityLog)
                .where(ActivityLog.created_at < cutoff_date)
                .where(ActivityLog.status == "active")
                .values(status="archived")
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            logger.info(f"Archived {result.rowcount} old activities")
            return result.rowcount
            
        except Exception as e:
            logger.error(f"Error archiving activities: {e}")
            await db.rollback()
            raise


# Convenience functions for common activity types

async def log_application_activity(
    db: AsyncSession,
    activity_type: str,
    application_id: int,
    application_name: str,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log an application-related activity"""
    # Create activity directly to avoid enum case issues
    activity = ActivityLog(
        activity_type=activity_type.lower(),  # Ensure lowercase for PostgreSQL enum
        priority="medium",
        title=f"{application_name}",
        description=description or f"Application {activity_type.replace('_', ' ')}",
        user_id=user_id,
        user_name=user_name,
        entity_type="application",
        entity_id=application_id,
        entity_name=application_name,
        extra_data=metadata,
        tags=["application"],
        status="active",
        is_read=False
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


async def log_application_update_activity(
    db: AsyncSession,
    application_id: int,
    application_name: str,
    updated_fields: Dict[str, Any],
    user_id: Optional[int] = None,
    user_name: Optional[str] = None
):
    """Log application update with changed fields"""
    changes_desc = ", ".join([f"{k}: {v}" for k, v in updated_fields.items() if k not in ["updated_at", "id"]])
    description = f"Application updated - {changes_desc}" if changes_desc else "Application updated"
    
    return await log_application_activity(
        db=db,
        activity_type="application_updated",
        application_id=application_id,
        application_name=application_name,
        user_id=user_id,
        user_name=user_name,
        description=description,
        metadata={"changes": updated_fields}
    )


async def log_vendor_activity(
    db: AsyncSession,
    activity_type: str,
    vendor_id: int,
    vendor_name: str,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log a vendor-related activity"""
    # Create activity directly to avoid enum case issues
    activity = ActivityLog(
        activity_type=activity_type.lower(),  # Ensure lowercase for PostgreSQL enum
        priority="medium",
        title=f"{vendor_name}",
        description=description or f"Vendor {activity_type.replace('_', ' ')}",
        user_id=user_id,
        user_name=user_name,
        entity_type="vendor",
        entity_id=vendor_id,
        entity_name=vendor_name,
        extra_data=metadata,
        tags=["vendor", "compliance"],
        status="active",
        is_read=False
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


async def log_vendor_update_activity(
    db: AsyncSession,
    vendor_id: int,
    vendor_name: str,
    updated_fields: Dict[str, Any],
    user_id: Optional[int] = None,
    user_name: Optional[str] = None
):
    """Log vendor update with changed fields"""
    changes_desc = ", ".join([f"{k}: {v}" for k, v in updated_fields.items() if k not in ["updated_at", "id"]])
    description = f"Vendor updated - {changes_desc}" if changes_desc else "Vendor updated"
    
    return await log_vendor_activity(
        db=db,
        activity_type="vendor_updated",
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        user_id=user_id,
        user_name=user_name,
        description=description,
        metadata={"changes": updated_fields}
    )


async def log_vulnerability_activity(
    db: AsyncSession,
    activity_type: str,
    vulnerability_id: int,
    vulnerability_title: str,
    severity: str,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log a vulnerability-related activity"""
    priority = ActivityPriority.HIGH if severity in ["critical", "high"] else ActivityPriority.MEDIUM
    
    activity_data = ActivityLogCreate(
        activity_type=activity_type,
        priority=priority,
        title=f"{vulnerability_title}",
        description=description or f"Vulnerability {activity_type.replace('_', ' ')}",
        user_id=user_id,
        user_name=user_name,
        entity_type="vulnerability",
        entity_id=vulnerability_id,
        entity_name=vulnerability_title,
        extra_data={**(metadata or {}), "severity": severity},
        tags=["vulnerability", "security", severity]
    )
    
    return await ActivityLogService.create_activity(db, activity_data)


async def log_exception_activity(
    db: AsyncSession,
    activity_type: str,
    exception_id: int,
    exception_name: str,
    severity: str,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    description: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """Log an exception-related activity"""
    priority_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low"
    }
    priority = priority_map.get(severity.lower(), "medium")
    
    # Create activity directly to avoid enum case issues
    activity = ActivityLog(
        activity_type=activity_type.lower(),  # Ensure lowercase for PostgreSQL enum
        priority=priority,
        title=f"Exception: {exception_name}",
        description=description or f"Exception {activity_type.replace('_', ' ')}",
        user_id=user_id,
        user_name=user_name or "System",
        entity_type="exception",
        entity_id=exception_id,
        entity_name=exception_name,
        extra_data={**(extra_data or {}), "severity": severity},
        tags=["exception", "compliance", severity.lower()],
        status="active",
        is_read=False
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


async def log_exception_update_activity(
    db: AsyncSession,
    exception_id: int,
    exception_name: str,
    updated_fields: Dict[str, Any],
    severity: str = "medium",
    user_id: Optional[int] = None,
    user_name: Optional[str] = None
):
    """Log exception update with changed fields"""
    changes_desc = ", ".join([f"{k}: {v}" for k, v in updated_fields.items() if k not in ["updated_at", "id"]])
    description = f"Exception updated - {changes_desc}" if changes_desc else "Exception updated"
    
    return await log_exception_activity(
        db=db,
        activity_type="exception_updated",
        exception_id=exception_id,
        exception_name=exception_name,
        severity=severity,
        user_id=user_id,
        user_name=user_name,
        description=description,
        extra_data={"changes": updated_fields}
    )


async def log_eosl_activity(
    db: AsyncSession,
    activity_type: str,
    asset_id: int,
    asset_name: str,
    risk_level: str,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    description: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """Log an EOSL asset-related activity"""
    priority_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low"
    }
    priority = priority_map.get(risk_level.lower(), "medium")
    
    # Create activity directly to avoid enum case issues
    activity = ActivityLog(
        activity_type=activity_type.lower(),  # Ensure lowercase for PostgreSQL enum
        priority=priority,
        title=f"EOSL Asset: {asset_name}",
        description=description or f"EOSL asset {activity_type.replace('_', ' ')}",
        user_id=user_id,
        user_name=user_name or "System",
        entity_type="eosl",
        entity_id=asset_id,
        entity_name=asset_name,
        extra_data={**(extra_data or {}), "risk_level": risk_level},
        tags=["eosl", "lifecycle", risk_level.lower()],
        status="active",
        is_read=False
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


async def log_eosl_update_activity(
    db: AsyncSession,
    asset_id: int,
    asset_name: str,
    updated_fields: Dict[str, Any],
    risk_level: str = "medium",
    user_id: Optional[int] = None,
    user_name: Optional[str] = None
):
    """Log EOSL asset update with changed fields"""
    changes_desc = ", ".join([f"{k}: {v}" for k, v in updated_fields.items() if k not in ["updated_at", "id"]])
    description = f"EOSL asset updated - {changes_desc}" if changes_desc else "EOSL asset updated"
    
    return await log_eosl_activity(
        db=db,
        activity_type="eosl_asset_updated",
        asset_id=asset_id,
        asset_name=asset_name,
        risk_level=risk_level,
        user_id=user_id,
        user_name=user_name,
        description=description,
        extra_data={"changes": updated_fields}
    )