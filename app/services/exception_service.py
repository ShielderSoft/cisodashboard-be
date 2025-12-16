from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import date, timedelta
import logging

from app.crud.crud_exception import exception_crud
from app.schemas.exception import (
    ExceptionCreate, ExceptionUpdate, ExceptionResponse, 
    ExceptionListResponse, ExceptionFilters, ExceptionStats
)
from app.models.models import Exception as ExceptionModel, ExceptionStatus

logger = logging.getLogger(__name__)


class ExceptionService:
    """Exception service layer for business logic"""

    def __init__(self):
        self.crud = exception_crud

    async def create_exception(
        self, 
        db: AsyncSession, 
        exception_data: ExceptionCreate,
        current_user_id: Optional[int] = None
    ) -> ExceptionResponse:
        """Create a new exception"""
        try:
            # Business logic validations
            await self._validate_exception_create(db, exception_data)
            
            # Create exception with audit trail
            exception_dict = exception_data.model_dump()
            exception_dict["created_by_id"] = current_user_id
            
            # Auto-set status based on dates
            if exception_data.end_date and exception_data.end_date < date.today():
                exception_dict["status"] = ExceptionStatus.EXPIRED
            elif exception_data.start_date <= date.today():
                exception_dict["status"] = ExceptionStatus.ACTIVE
            else:
                exception_dict["status"] = ExceptionStatus.PENDING
            
            exception = await self.crud.create(db, obj_in=exception_dict)
            
            return await self._exception_to_response(exception)
            
        except Exception as e:
            logger.error(f"Error in create_exception service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create exception"
            )

    async def get_exception(
        self, 
        db: AsyncSession, 
        exception_id: int,
        current_user_id: Optional[int] = None
    ) -> ExceptionResponse:
        """Get exception by ID"""
        try:
            exception = await self.crud.get(db, exception_id)
            if not exception:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exception not found"
                )
            
            return await self._exception_to_response(exception)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_exception service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve exception"
            )

    async def get_exceptions(
        self, 
        db: AsyncSession, 
        filters: ExceptionFilters,
        current_user_id: Optional[int] = None
    ) -> ExceptionListResponse:
        """Get exceptions with filtering and pagination"""
        try:
            # Auto-update expired exceptions before querying
            await self.crud.update_expired_exceptions(db, filters.organization_id)
            
            exceptions, total = await self.crud.get_multi_with_filters(db, filters, current_user_id)
            
            # Convert to response format
            exception_responses = []
            for exception in exceptions:
                exception_response = await self._exception_to_response(exception)
                exception_responses.append(exception_response)
            
            # Calculate pagination
            pages = (total + filters.size - 1) // filters.size
            
            return ExceptionListResponse(
                exceptions=exception_responses,
                total=total,
                page=filters.page,
                size=filters.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error in get_exceptions service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve exceptions"
            )

    async def update_exception(
        self, 
        db: AsyncSession, 
        exception_id: int, 
        exception_data: ExceptionUpdate,
        current_user_id: Optional[int] = None
    ) -> ExceptionResponse:
        """Update exception"""
        try:
            exception = await self.crud.get(db, exception_id)
            if not exception:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exception not found"
                )
            
            # Business logic validations
            await self._validate_exception_update(db, exception_id, exception_data)
            
            # Update exception
            updated_exception = await self.crud.update(
                db, 
                db_obj=exception, 
                obj_in=exception_data
            )
            
            return await self._exception_to_response(updated_exception)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_exception service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update exception"
            )

    async def delete_exception(
        self, 
        db: AsyncSession, 
        exception_id: int,
        current_user_id: Optional[int] = None
    ) -> bool:
        """Delete exception"""
        try:
            exception = await self.crud.get(db, exception_id)
            if not exception:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exception not found"
                )
            
            await self.crud.remove(db, id=exception_id)
            logger.info(f"Deleted exception: {exception.exception_name} (ID: {exception_id})")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in delete_exception service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete exception"
            )

    async def approve_exception(
        self, 
        db: AsyncSession, 
        exception_id: int,
        approval_status: str,
        current_user_id: Optional[int] = None
    ) -> ExceptionResponse:
        """Approve or reject an exception"""
        try:
            if approval_status not in ["approved", "rejected"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid approval status. Must be 'approved' or 'rejected'"
                )
            
            exception = await self.crud.approve_exception(
                db, exception_id, current_user_id, approval_status
            )
            
            if not exception:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exception not found"
                )
            
            return await self._exception_to_response(exception)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in approve_exception service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to approve exception"
            )

    async def get_expiring_exceptions(
        self, 
        db: AsyncSession, 
        days: int = 30,
        organization_id: Optional[int] = None
    ) -> List[ExceptionResponse]:
        """Get exceptions expiring soon"""
        try:
            exceptions = await self.crud.get_expiring_soon(db, days, organization_id)
            
            exception_responses = []
            for exception in exceptions:
                exception_response = await self._exception_to_response(exception)
                exception_responses.append(exception_response)
            
            return exception_responses
            
        except Exception as e:
            logger.error(f"Error in get_expiring_exceptions service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve expiring exceptions"
            )

    async def get_exception_stats(
        self, 
        db: AsyncSession,
        organization_id: Optional[int] = None
    ) -> ExceptionStats:
        """Get exception statistics"""
        try:
            stats = await self.crud.get_stats(db, organization_id)
            return ExceptionStats(**stats)
            
        except Exception as e:
            logger.error(f"Error in get_exception_stats service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve exception statistics"
            )

    async def _validate_exception_create(
        self, 
        db: AsyncSession, 
        exception_data: ExceptionCreate
    ):
        """Validate exception creation data"""
        # Check for duplicate exception name
        existing = await self.crud.get_by_name(
            db, 
            exception_data.exception_name, 
            exception_data.organization_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exception with name '{exception_data.exception_name}' already exists"
            )
        
        # Validate date range
        if exception_data.end_date and exception_data.end_date <= exception_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

    async def _validate_exception_update(
        self, 
        db: AsyncSession, 
        exception_id: int, 
        exception_data: ExceptionUpdate
    ):
        """Validate exception update data"""
        # Check for duplicate exception name (if name is being updated)
        if exception_data.exception_name:
            existing = await self.crud.get_by_name(db, exception_data.exception_name)
            if existing and existing.id != exception_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exception with name '{exception_data.exception_name}' already exists"
                )

    async def _exception_to_response(self, exception: ExceptionModel) -> ExceptionResponse:
        """Convert exception model to response schema"""
        try:
            # Calculate computed fields
            is_expired = False
            days_remaining = None
            
            if exception.end_date:
                today = date.today()
                is_expired = exception.end_date < today
                if not is_expired:
                    days_remaining = (exception.end_date - today).days
            
            return ExceptionResponse(
                id=exception.id,
                exception_name=exception.exception_name,
                category=exception.category,
                severity=exception.severity,
                status=exception.status,
                start_date=exception.start_date,
                end_date=exception.end_date,
                comments=exception.comments,
                risk_assessment=exception.risk_assessment,
                mitigation_plan=exception.mitigation_plan,
                approval_status=exception.approval_status,
                approved_by_id=exception.approved_by_id,
                approved_at=exception.approved_at,
                organization_id=exception.organization_id,
                created_by_id=exception.created_by_id,
                assigned_to_id=exception.assigned_to_id,
                created_at=exception.created_at,
                updated_at=exception.updated_at,
                is_expired=is_expired,
                days_remaining=days_remaining
            )
        except Exception as e:
            logger.error(f"Error converting exception to response: {e}")
            raise


# Create service instance
exception_service = ExceptionService()