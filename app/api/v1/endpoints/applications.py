from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from io import BytesIO
import pandas as pd
import logging
from typing import Optional, List

from app.db.session import get_session
from app.models.models import Application, ApplicationType
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

@router.post("/bulk-upload")
async def bulk_upload_applications(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session)
):
    """
    Bulk upload applications from Excel file (.xlsx, .xls)
    
    Expected columns:
    - Application Name
    - Application Type
    - Owner
    - Vendor
    - Description
    - URL
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)."
        )

    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Failed to read Excel file: {str(e)}"
        )

    # Mapping of technical column names to potential Excel column names
    column_mapping = {
        "name": ["Application Name", "App Name", "Name"],
        "type": ["Application Type", "App Type", "Type"],
        "owner": ["Owner"],
        "vendor": ["Vendor", "Vendor Name"],
        "description": ["Description", "App Description"],
        "url": ["URL", "Link", "App URL"]
    }
    
    # Find actual columns in df
    found_mapping = {}
    missing = []
    
    for tech_name, variations in column_mapping.items():
        found = False
        for var in variations:
            # Check for exact case
            if var in df.columns:
                found_mapping[tech_name] = var
                found = True
                break
            # Check case-insensitive
            for col in df.columns:
                if str(col).strip().lower() == var.lower():
                    found_mapping[tech_name] = col
                    found = True
                    break
            if found: break
        
        # Only name and type might be strictly required or I can defaults
        if not found and tech_name in ["name", "type"]:
            missing.append(variations[0])

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Missing required columns: {', '.join(missing)}"
        )

    total = len(df)
    success = 0
    failed = 0
    errors = []

    # Fetch existing names and URLs for duplicate check
    existing_apps_query = await db.execute(select(Application.name, Application.url))
    existing_rows = existing_apps_query.all()
    existing_names = set(row[0] for row in existing_rows)
    existing_urls = set(row[1] for row in existing_rows if row[1])

    # Map for Application Type Enum
    type_map = {
        "web": ApplicationType.WEB_APPLICATION,
        "mobile": ApplicationType.MOBILE_APPLICATION,
        "desktop": ApplicationType.DESKTOP_APPLICATION,
        "api": ApplicationType.API_SERVICE,
        "database": ApplicationType.DATABASE,
        "infrastructure": ApplicationType.INFRASTRUCTURE,
        "third party": ApplicationType.THIRD_PARTY,
        "external": ApplicationType.WEB_APPLICATION, # fallback
        "internal": ApplicationType.WEB_APPLICATION, # fallback
    }

    total = len(df)
    success = 0
    failed = 0
    successful_apps = []
    errors = []

    # ... existing code for existing_names and type_map ...
    
    new_apps = []
    for idx, row in df.iterrows():
        row_errors = []
        
        # Get values using found mapping
        name = str(row.get(found_mapping.get("name"), "")).strip() if "name" in found_mapping else ""
        app_type_str = str(row.get(found_mapping.get("type"), "")).strip().lower() if "type" in found_mapping else ""
        owner = str(row.get(found_mapping.get("owner"), "")).strip() if "owner" in found_mapping else ""
        vendor = str(row.get(found_mapping.get("vendor"), "")).strip() if "vendor" in found_mapping else ""
        description = str(row.get(found_mapping.get("description"), "")).strip() if "description" in found_mapping else ""
        url = str(row.get(found_mapping.get("url"), "")).strip() if "url" in found_mapping else ""

        if not name:
            row_errors.append("Application Name is required")
        
        if name and name in existing_names:
            row_errors.append(f"Application with name '{name}' already exists")

        # Map application type
        app_type = type_map.get(app_type_str)
        if not app_type:
            # Try to match by value if key not found
            for enum_val in ApplicationType:
                if enum_val.value == app_type_str.replace(" ", "_"):
                    app_type = enum_val
                    break
            
            if not app_type:
                app_type = ApplicationType.WEB_APPLICATION # Default fallback

        if row_errors:
            failed += 1
            errors.append({"row": idx + 2, "name": name, "errors": row_errors})
            continue

        try:
            app = Application(
                name=name,
                application_type=app_type,
                owner=owner if owner else None,
                vendor_name=vendor if vendor else None,
                description=description if description else None,
                url=url if url else None,
                risk_level="medium" # Default
            )
            new_apps.append(app)
            existing_names.add(name)
            successful_apps.append(name)
            success += 1
        except Exception as e:
            failed += 1
            errors.append({"row": idx + 2, "name": name, "errors": [str(e)]})

    if new_apps:
        try:
            db.add_all(new_apps)
            await db.commit()
            
            # Log bulk activity
            await log_application_activity(
                db=db,
                activity_type="application_created",
                application_id=None,
                application_name="Bulk Upload",
                user_id=None,
                user_name="System User",
                description=f"Bulk upload successful: {success} applications created",
                metadata={"total": total, "success": success, "failed": failed}
            )
        except Exception as e:
            await db.rollback()
            logger.error(f"Database error during bulk insert: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save applications to database"
            )

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "successful_apps": successful_apps,
        "errors": errors
    }


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