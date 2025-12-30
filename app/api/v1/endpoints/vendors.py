from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_session
from app.services.vendor_service import vendor_service
from app.services.activity_service import log_vendor_activity
from app.schemas.vendor import (
    VendorCreate, VendorUpdate, VendorResponse, VendorListResponse,
    VendorFilterParams, VendorDashboardResponse, StandardOptionsResponse,
    VendorBulkUpdateRequest, VendorBulkResponse, ComplianceStandardEnum
)
from app.models.models import RiskLevel, ComplianceStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_data: VendorCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new vendor
    
    This endpoint creates a new vendor with the provided information.
    If a compliance standard is specified, it will also create an initial
    compliance record for that standard.
    """
    # Create the vendor
    vendor = await vendor_service.create_vendor(db, vendor_data)
    
    # Log activity
    try:
        await log_vendor_activity(
            db=db,
            activity_type="vendor_created",
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            user_id=None,
            user_name="System User",
            description=f"New vendor '{vendor.name}' added to the system",
            metadata={
                "category": vendor.category,
                "risk_level": str(vendor.risk_level) if vendor.risk_level else "medium",
                "compliance_status": str(vendor.compliance_status) if vendor.compliance_status else "pending"
            }
        )
    except Exception as e:
        logger.error(f"Failed to log vendor activity: {e}")
    
    return vendor


@router.get("/", response_model=VendorListResponse)
async def get_vendors(
    search: Optional[str] = Query(None, description="Search in vendor name or description"),
    category: Optional[str] = Query(None, description="Filter by vendor category"),
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk level"),
    compliance_status: Optional[ComplianceStatus] = Query(None, description="Filter by compliance status"),
    standard: Optional[ComplianceStandardEnum] = Query(None, description="Filter by compliance standard"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get filtered list of vendors
    
    Returns a paginated list of vendors with optional filtering and sorting.
    Supports searching by name and description, filtering by category, risk level,
    compliance status, and compliance standard (returns vendors assigned to that standard).
    """
    filters = VendorFilterParams(
        search=search,
        category=category,
        risk_level=risk_level,
        compliance_status=compliance_status,
        standard=standard,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return await vendor_service.get_vendors(db, filters)


@router.get("/dashboard", response_model=VendorDashboardResponse)
async def get_vendor_dashboard(
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendor dashboard data
    
    Returns comprehensive dashboard information including:
    - Vendor statistics (total, compliant, non-compliant, etc.)
    - Risk level distribution
    - Compliance status distribution
    - Recent vendors
    - Expiring certificates
    """
    return await vendor_service.get_vendor_dashboard(db)


@router.get("/standards", response_model=StandardOptionsResponse)
async def get_compliance_standards():
    """
    Get available compliance standards
    
    Returns a list of all available compliance standards that can be
    used when creating vendors. This is used to populate dropdown
    options in the frontend.
    """
    return await vendor_service.get_standard_options()


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendor by ID
    
    Returns detailed information about a specific vendor including
    compliance records count and active vulnerabilities count.
    """
    return await vendor_service.get_vendor(db, vendor_id)


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    db: AsyncSession = Depends(get_session)
):
    """
    Update vendor
    
    Updates an existing vendor with the provided information.
    Only provided fields will be updated, others remain unchanged.
    """
    from app.services.activity_service import log_vendor_update_activity
    
    result = await vendor_service.update_vendor(db, vendor_id, vendor_data)
    
    # Log the update activity
    try:
        updated_fields = vendor_data.dict(exclude_unset=True)
        await log_vendor_update_activity(
            db=db,
            vendor_id=result.id,
            vendor_name=result.name,
            updated_fields=updated_fields,
            user_id=None,
            user_name="System User"
        )
    except Exception as e:
        logger.warning(f"Failed to log vendor update activity: {str(e)}")
    
    return result


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Delete vendor
    
    Permanently deletes a vendor and all associated records.
    This action cannot be undone.
    """
    await vendor_service.delete_vendor(db, vendor_id)


@router.put("/bulk", response_model=VendorBulkResponse)
async def bulk_update_vendors(
    bulk_request: VendorBulkUpdateRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Bulk update vendors
    
    Updates multiple vendors with the same information.
    Returns the count of successful and failed updates.
    """
    # This is a simplified version - you'd implement this in the service layer
    return VendorBulkResponse(
        success_count=0,
        failed_count=len(bulk_request.vendor_ids),
        errors=[{"error": "Bulk update not yet implemented"}]
    )


# Additional endpoints for vendor compliance management

@router.get("/{vendor_id}/compliance", response_model=List[dict])
async def get_vendor_compliance_records(
    vendor_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendor compliance records
    
    Returns all compliance records for a specific vendor.
    """
    # TODO: Implement vendor compliance records retrieval
    return []


@router.post("/{vendor_id}/compliance", response_model=dict)
async def create_vendor_compliance_record(
    vendor_id: int,
    compliance_data: dict,
    db: AsyncSession = Depends(get_session)
):
    """
    Create vendor compliance record
    
    Adds a new compliance record for a vendor.
    """
    # TODO: Implement vendor compliance record creation
    return {"message": "Compliance record created"}


@router.get("/{vendor_id}/vulnerabilities", response_model=List[dict])
async def get_vendor_vulnerabilities(
    vendor_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendor-related vulnerabilities
    
    Returns all vulnerabilities associated with a specific vendor.
    """
    # TODO: Implement vendor vulnerabilities retrieval
    return []


@router.get("/{vendor_id}/risk-assessment", response_model=dict)
async def get_vendor_risk_assessment(
    vendor_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendor risk assessment
    
    Returns the latest risk assessment for a vendor.
    """
    # TODO: Implement vendor risk assessment retrieval
    return {"message": "Risk assessment data"}


@router.post("/{vendor_id}/risk-assessment", response_model=dict)
async def create_vendor_risk_assessment(
    vendor_id: int,
    assessment_data: dict,
    db: AsyncSession = Depends(get_session)
):
    """
    Create vendor risk assessment
    
    Creates a new risk assessment for a vendor.
    """
    # TODO: Implement vendor risk assessment creation
    return {"message": "Risk assessment created"}