"""API endpoints for application management"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_session
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationFilterParams,
    ApplicationStatistics,
    ApplicationTypeEnum,
    RiskLevelEnum
)
from app.services.application_service import application_service
from app.services.activity_service import log_application_activity

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    *,
    db: AsyncSession = Depends(get_session),
    application_in: ApplicationCreate
):
    """
    Create a new application with optional vulnerabilities
    
    - **name**: Application name (required)
    - **type**: Application type (internal/external/mobile/web/api) (required)
    - **description**: Application description
    - **owner**: Owner name or email
    - **vendor**: Vendor name if third-party application
    - **vulnerabilities**: Optional array of vulnerabilities to create with the application
    """
    # Create the application
    app = await application_service.create_application(
        db=db,
        application_in=application_in
    )
    
    # Log activity
    try:
        # Fetch the actual application model to get database fields
        from app.crud.crud_application import application as crud_app
        db_app = await crud_app.get(db, id=app.id)
        
        await log_application_activity(
            db=db,
            activity_type="application_created",
            application_id=app.id,
            application_name=app.name,
            user_id=None,
            user_name="System User",
            description=f"New application '{app.name}' created",
            metadata={
                "type": str(db_app.application_type.value) if db_app.application_type else "unknown",
                "risk_level": str(db_app.risk_level.value) if db_app.risk_level else "medium",
                "owner": db_app.owner
            }
        )
    except Exception as e:
        logger.error(f"Failed to log application activity: {e}")
    
    return app


@router.get("/", response_model=ApplicationListResponse)
async def get_applications(
    *,
    db: AsyncSession = Depends(get_session),
    search: Optional[str] = Query(None, description="Search in name, description, owner"),
    type: Optional[ApplicationTypeEnum] = Query(None, description="Filter by application type"),
    risk_level: Optional[RiskLevelEnum] = Query(None, description="Filter by risk level"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size")
):
    """
    Get applications with filtering and pagination
    
    Query parameters:
    - **search**: Search in name, description, owner
    - **type**: Filter by application type (internal/external/mobile/web/api)
    - **risk_level**: Filter by risk level (critical/high/medium/low)
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 50, max: 100)
    """
    filters = ApplicationFilterParams(
        search=search,
        type=type,
        risk_level=risk_level,
        page=page,
        size=size
    )
    
    return await application_service.get_applications(db=db, filters=filters)


@router.get("/statistics", response_model=ApplicationStatistics)
async def get_application_statistics(
    *,
    db: AsyncSession = Depends(get_session)
):
    """
    Get application statistics
    
    Returns counts by type, risk level, and vulnerability association
    """
    return await application_service.get_statistics(db=db)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    *,
    db: AsyncSession = Depends(get_session),
    application_id: int
):
    """
    Get application by ID
    """
    return await application_service.get_application_by_id(
        db=db,
        application_id=application_id
    )


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    *,
    db: AsyncSession = Depends(get_session),
    application_id: int,
    application_in: ApplicationUpdate
):
    """
    Update application
    
    All fields are optional. Only provided fields will be updated.
    """
    from app.services.activity_service import log_application_update_activity
    
    result = await application_service.update_application(
        db=db,
        application_id=application_id,
        application_in=application_in
    )
    
    # Log the update activity
    try:
        updated_fields = application_in.dict(exclude_unset=True)
        await log_application_update_activity(
            db=db,
            application_id=result.id,
            application_name=result.name,
            updated_fields=updated_fields,
            user_id=None,
            user_name="System User"
        )
    except Exception as e:
        logger.warning(f"Failed to log application update activity: {str(e)}")
    
    return result


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    *,
    db: AsyncSession = Depends(get_session),
    application_id: int
):
    """
    Delete application
    
    Note: This will also affect associated vulnerabilities depending on cascade settings.
    """
    await application_service.delete_application(
        db=db,
        application_id=application_id
    )
    return None