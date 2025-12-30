from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, datetime

from app.db.session import get_session
from app.schemas.exception import (
    ExceptionCreate, ExceptionUpdate, ExceptionResponse,
    ExceptionListResponse, ExceptionFilters, ExceptionStats,
    ExceptionCategoriesResponse
)
from app.services.exception_service import exception_service
from app.services.activity_service import log_exception_activity
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ExceptionResponse, status_code=status.HTTP_201_CREATED)
async def create_exception(
    exception_data: ExceptionCreate,
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Create a new exception.
    
    - **exception_name**: Name of the exception
    - **category**: Exception category (compliance, technical, operational, other)
    - **severity**: Exception severity (critical, high, medium, low)
    - **status**: Exception status (active, expired, pending)
    - **start_date**: Exception start date
    - **end_date**: Exception end date (optional)
    - **comments**: Additional comments (optional)
    """
    # Create the exception
    new_exception = await exception_service.create_exception(db, exception_data, current_user_id)
    
    # Log activity
    try:
        await log_exception_activity(
            db=db,
            activity_type="exception_created",
            exception_id=new_exception.id,
            exception_name=new_exception.exception_name,
            severity=exception_data.severity,
            user_id=current_user_id,
            user_name="System User",  # TODO: Get from authenticated user
            description=f"New exception '{new_exception.exception_name}' created with {exception_data.severity} severity",
            extra_data={
                "category": exception_data.category,
                "status": exception_data.status,
                "start_date": str(exception_data.start_date) if exception_data.start_date else None,
                "end_date": str(exception_data.end_date) if exception_data.end_date else None
            }
        )
    except Exception as e:
        logger.error(f"Failed to log exception activity: {e}")
    
    return new_exception


@router.get("/", response_model=ExceptionListResponse)
async def get_exceptions(
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in exception name and comments"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned user"),
    created_by_id: Optional[int] = Query(None, description="Filter by creator"),
    start_date_from: Optional[str] = Query(None, description="Filter start date from (YYYY-MM-DD)"),
    start_date_to: Optional[str] = Query(None, description="Filter start date to (YYYY-MM-DD)"),
    end_date_from: Optional[str] = Query(None, description="Filter end date from (YYYY-MM-DD)"),
    end_date_to: Optional[str] = Query(None, description="Filter end date to (YYYY-MM-DD)"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Get exceptions with filtering and pagination.
    
    Returns a paginated list of exceptions based on the provided filters.
    """
    # Convert string dates to date objects if provided
    filters_dict = {
        "category": category,
        "severity": severity,
        "status": status,
        "search": search,
        "organization_id": organization_id,
        "assigned_to_id": assigned_to_id,
        "created_by_id": created_by_id,
        "approval_status": approval_status,
        "page": page,
        "size": size
    }
    
    # Parse date strings
    if start_date_from:
        try:
            filters_dict["start_date_from"] = datetime.strptime(start_date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date_from format. Use YYYY-MM-DD"
            )
    
    if start_date_to:
        try:
            filters_dict["start_date_to"] = datetime.strptime(start_date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date_to format. Use YYYY-MM-DD"
            )
    
    if end_date_from:
        try:
            filters_dict["end_date_from"] = datetime.strptime(end_date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date_from format. Use YYYY-MM-DD"
            )
    
    if end_date_to:
        try:
            filters_dict["end_date_to"] = datetime.strptime(end_date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date_to format. Use YYYY-MM-DD"
            )
    
    filters = ExceptionFilters(**filters_dict)
    return await exception_service.get_exceptions(db, filters, current_user_id)


@router.get("/{exception_id}", response_model=ExceptionResponse)
async def get_exception(
    exception_id: int,
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Get exception by ID.
    """
    return await exception_service.get_exception(db, exception_id, current_user_id)


@router.put("/{exception_id}", response_model=ExceptionResponse)
async def update_exception(
    exception_id: int,
    exception_data: ExceptionUpdate,
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Update an existing exception.
    """
    from app.services.activity_service import log_exception_update_activity
    
    result = await exception_service.update_exception(db, exception_id, exception_data, current_user_id)
    
    # Log the update activity
    try:
        updated_fields = exception_data.dict(exclude_unset=True)
        await log_exception_update_activity(
            db=db,
            exception_id=result.id,
            exception_name=result.exception_name,
            updated_fields=updated_fields,
            severity=result.severity,
            user_id=current_user_id,
            user_name="System User"
        )
    except Exception as e:
        logger.warning(f"Failed to log exception update activity: {str(e)}")
    
    return result


@router.patch("/{exception_id}/expiry", response_model=ExceptionResponse)
async def update_exception_expiry(
    exception_id: int,
    end_date: date = Query(..., description="New expiry date (YYYY-MM-DD)"),
    reason: Optional[str] = Query(None, description="Reason for expiry update"),
    notes: Optional[str] = Query(None, description="Additional notes"),
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Update the expiry date of an exception.
    
    - **exception_id**: ID of the exception to update
    - **end_date**: New expiry date
    - **reason**: Reason for changing the expiry date
    - **notes**: Additional notes about the change
    """
    # Create update data
    update_data = ExceptionUpdate(
        end_date=end_date,
        comments=f"{reason or 'Expiry updated'}\n{notes or ''}".strip()
    )
    return await exception_service.update_exception(db, exception_id, update_data, current_user_id)


@router.delete("/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exception(
    exception_id: int,
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Delete an exception.
    """
    await exception_service.delete_exception(db, exception_id, current_user_id)


@router.post("/{exception_id}/approve", response_model=ExceptionResponse)
async def approve_exception(
    exception_id: int,
    approval_status: str = Query(..., regex="^(approved|rejected)$", description="Approval status"),
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Approve or reject an exception.
    
    - **approval_status**: Either 'approved' or 'rejected'
    """
    return await exception_service.approve_exception(db, exception_id, approval_status, current_user_id)


@router.get("/expiring/soon", response_model=List[ExceptionResponse])
async def get_expiring_exceptions(
    days: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Get exceptions expiring within the specified number of days.
    """
    return await exception_service.get_expiring_exceptions(db, days, organization_id)


@router.get("/stats/overview", response_model=ExceptionStats)
async def get_exception_statistics(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    db: AsyncSession = Depends(get_session),
    current_user_id: Optional[int] = None  # TODO: Add authentication dependency
):
    """
    Get exception statistics and metrics.
    """
    return await exception_service.get_exception_stats(db, organization_id)


@router.get("/meta/options", response_model=ExceptionCategoriesResponse)
async def get_exception_options():
    """
    Get available options for exception categories, severities, and statuses.
    This endpoint provides dropdown options for the frontend forms.
    """
    return ExceptionCategoriesResponse()