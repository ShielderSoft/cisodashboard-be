from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from datetime import date, datetime, timedelta
import logging

from app.crud.base import CRUDBase
from app.models.models import Exception as ExceptionModel, ExceptionStatus, ExceptionCategory, ExceptionSeverity
from app.schemas.exception import ExceptionCreate, ExceptionUpdate, ExceptionFilters

logger = logging.getLogger(__name__)


class CRUDException(CRUDBase[ExceptionModel, ExceptionCreate, ExceptionUpdate]):
    """CRUD operations for Exception model"""

    async def get_multi_with_filters(
        self, 
        db: AsyncSession, 
        filters: ExceptionFilters,
        current_user_id: Optional[int] = None
    ) -> tuple[List[ExceptionModel], int]:
        """Get exceptions with filtering and pagination"""
        try:
            # Build base query
            query = select(ExceptionModel).options(
                selectinload(ExceptionModel.created_by),
                selectinload(ExceptionModel.assigned_to),
                selectinload(ExceptionModel.approved_by),
                selectinload(ExceptionModel.organization)
            )
            
            # Apply filters
            conditions = []
            
            # Filter by category
            if filters.category:
                conditions.append(ExceptionModel.category == filters.category)
            
            # Filter by severity
            if filters.severity:
                conditions.append(ExceptionModel.severity == filters.severity)
            
            # Filter by status
            if filters.status:
                conditions.append(ExceptionModel.status == filters.status)
            
            # Search in exception name and comments
            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        ExceptionModel.exception_name.ilike(search_term),
                        ExceptionModel.comments.ilike(search_term)
                    )
                )
            
            # Filter by organization
            if filters.organization_id:
                conditions.append(ExceptionModel.organization_id == filters.organization_id)
            
            # Filter by assigned user
            if filters.assigned_to_id:
                conditions.append(ExceptionModel.assigned_to_id == filters.assigned_to_id)
            
            # Filter by creator
            if filters.created_by_id:
                conditions.append(ExceptionModel.created_by_id == filters.created_by_id)
            
            # Filter by start date range
            if filters.start_date_from:
                conditions.append(ExceptionModel.start_date >= filters.start_date_from)
            if filters.start_date_to:
                conditions.append(ExceptionModel.start_date <= filters.start_date_to)
            
            # Filter by end date range
            if filters.end_date_from:
                conditions.append(ExceptionModel.end_date >= filters.end_date_from)
            if filters.end_date_to:
                conditions.append(ExceptionModel.end_date <= filters.end_date_to)
            
            # Filter by approval status
            if filters.approval_status:
                conditions.append(ExceptionModel.approval_status == filters.approval_status)
            
            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count(ExceptionModel.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Apply ordering
            query = query.order_by(desc(ExceptionModel.created_at))
            
            # Apply pagination
            offset = (filters.page - 1) * filters.size
            query = query.offset(offset).limit(filters.size)
            
            # Execute query
            result = await db.execute(query)
            exceptions = result.scalars().all()
            
            logger.info(f"Retrieved {len(exceptions)} exceptions with filters")
            return list(exceptions), total
            
        except Exception as e:
            logger.error(f"Error in get_multi_with_filters: {str(e)}")
            raise

    async def get_by_name(
        self, 
        db: AsyncSession, 
        exception_name: str,
        organization_id: Optional[int] = None
    ) -> Optional[ExceptionModel]:
        """Get exception by name"""
        try:
            query = select(ExceptionModel).where(ExceptionModel.exception_name == exception_name)
            
            if organization_id:
                query = query.where(ExceptionModel.organization_id == organization_id)
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error in get_by_name: {str(e)}")
            raise

    async def get_expiring_soon(
        self, 
        db: AsyncSession, 
        days: int = 30,
        organization_id: Optional[int] = None
    ) -> List[ExceptionModel]:
        """Get exceptions expiring within specified days"""
        try:
            cutoff_date = date.today() + timedelta(days=days)
            
            query = select(ExceptionModel).where(
                and_(
                    ExceptionModel.status == ExceptionStatus.ACTIVE,
                    ExceptionModel.end_date.isnot(None),
                    ExceptionModel.end_date <= cutoff_date,
                    ExceptionModel.end_date >= date.today()
                )
            ).options(
                selectinload(ExceptionModel.assigned_to),
                selectinload(ExceptionModel.organization)
            ).order_by(asc(ExceptionModel.end_date))
            
            if organization_id:
                query = query.where(ExceptionModel.organization_id == organization_id)
            
            result = await db.execute(query)
            exceptions = result.scalars().all()
            
            logger.info(f"Found {len(exceptions)} exceptions expiring within {days} days")
            return list(exceptions)
            
        except Exception as e:
            logger.error(f"Error in get_expiring_soon: {str(e)}")
            raise

    async def get_expired(
        self, 
        db: AsyncSession,
        organization_id: Optional[int] = None
    ) -> List[ExceptionModel]:
        """Get expired exceptions that should have status updated"""
        try:
            today = date.today()
            
            query = select(ExceptionModel).where(
                and_(
                    ExceptionModel.status == ExceptionStatus.ACTIVE,
                    ExceptionModel.end_date.isnot(None),
                    ExceptionModel.end_date < today
                )
            ).options(
                selectinload(ExceptionModel.assigned_to),
                selectinload(ExceptionModel.organization)
            )
            
            if organization_id:
                query = query.where(ExceptionModel.organization_id == organization_id)
            
            result = await db.execute(query)
            exceptions = result.scalars().all()
            
            logger.info(f"Found {len(exceptions)} expired exceptions")
            return list(exceptions)
            
        except Exception as e:
            logger.error(f"Error in get_expired: {str(e)}")
            raise

    async def update_expired_exceptions(
        self, 
        db: AsyncSession,
        organization_id: Optional[int] = None
    ) -> int:
        """Automatically update expired exceptions status"""
        try:
            expired_exceptions = await self.get_expired(db, organization_id)
            count = 0
            
            for exception in expired_exceptions:
                exception.status = ExceptionStatus.EXPIRED
                count += 1
            
            if count > 0:
                await db.commit()
                logger.info(f"Updated {count} expired exceptions")
            
            return count
            
        except Exception as e:
            logger.error(f"Error in update_expired_exceptions: {str(e)}")
            raise

    async def get_stats(
        self, 
        db: AsyncSession,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get exception statistics"""
        try:
            base_query = select(ExceptionModel)
            if organization_id:
                base_query = base_query.where(ExceptionModel.organization_id == organization_id)
            
            # Total exceptions
            total_result = await db.execute(
                select(func.count(ExceptionModel.id)).select_from(base_query.subquery())
            )
            total_exceptions = total_result.scalar() or 0
            
            # Exceptions by status
            status_result = await db.execute(
                select(ExceptionModel.status, func.count(ExceptionModel.id))
                .select_from(base_query.subquery())
                .group_by(ExceptionModel.status)
            )
            status_counts = {status.value: 0 for status in ExceptionStatus}
            for status, count in status_result.all():
                status_counts[status.value] = count
            
            # Exceptions by category
            category_result = await db.execute(
                select(ExceptionModel.category, func.count(ExceptionModel.id))
                .select_from(base_query.subquery())
                .group_by(ExceptionModel.category)
            )
            category_counts = {category.value: 0 for category in ExceptionCategory}
            for category, count in category_result.all():
                category_counts[category.value] = count
            
            # Exceptions by severity
            severity_result = await db.execute(
                select(ExceptionModel.severity, func.count(ExceptionModel.id))
                .select_from(base_query.subquery())
                .group_by(ExceptionModel.severity)
            )
            severity_counts = {severity.value: 0 for severity in ExceptionSeverity}
            for severity, count in severity_result.all():
                severity_counts[severity.value] = count
            
            # Expiring soon
            expiring_exceptions = await self.get_expiring_soon(db, days=30, organization_id=organization_id)
            expiring_soon = len(expiring_exceptions)
            
            stats = {
                "total_exceptions": total_exceptions,
                "active_exceptions": status_counts.get("active", 0),
                "expired_exceptions": status_counts.get("expired", 0),
                "pending_exceptions": status_counts.get("pending", 0),
                "by_category": category_counts,
                "by_severity": severity_counts,
                "expiring_soon": expiring_soon
            }
            
            logger.info(f"Generated exception statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in get_stats: {str(e)}")
            raise

    async def approve_exception(
        self, 
        db: AsyncSession, 
        exception_id: int, 
        approved_by_id: int,
        approval_status: str = "approved"
    ) -> Optional[Exception]:
        """Approve or reject an exception"""
        try:
            exception = await self.get(db, exception_id)
            if not exception:
                return None
            
            exception.approval_status = approval_status
            exception.approved_by_id = approved_by_id
            exception.approved_at = datetime.utcnow()
            
            if approval_status == "approved":
                exception.status = ExceptionStatus.ACTIVE
            
            await db.commit()
            await db.refresh(exception)
            
            logger.info(f"Exception {exception_id} {approval_status} by user {approved_by_id}")
            return exception
            
        except Exception as e:
            logger.error(f"Error in approve_exception: {str(e)}")
            raise


# Create instance
exception_crud = CRUDException(ExceptionModel)