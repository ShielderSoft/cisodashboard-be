from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.certificate_service import certificate_service
from app.schemas.certificate import (
    VendorCertificateCreate, VendorCertificateUpdate, VendorCertificateResponse
)

router = APIRouter()


@router.post("/", response_model=VendorCertificateResponse, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    certificate_data: VendorCertificateCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new vendor certificate
    
    This endpoint creates a new certificate for a vendor, optionally linked to an application.
    """
    return await certificate_service.create_certificate(db, certificate_data)


@router.get("/vendor/{vendor_id}", response_model=List[VendorCertificateResponse])
async def get_vendor_certificates(
    vendor_id: int,
    active_only: bool = Query(False, description="Only return non-expired certificates"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get all certificates for a vendor
    
    Returns all certificates associated with a specific vendor.
    Use active_only=true to filter out expired certificates.
    """
    return await certificate_service.get_vendor_certificates(db, vendor_id, active_only)


@router.get("/application/{application_id}", response_model=List[VendorCertificateResponse])
async def get_application_certificates(
    application_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get all certificates for an application
    
    Returns all certificates associated with a specific application.
    """
    return await certificate_service.get_application_certificates(db, application_id)


@router.get("/expiring", response_model=List[VendorCertificateResponse])
async def get_expiring_certificates(
    days: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get certificates expiring soon
    
    Returns certificates that will expire within the specified number of days.
    Default is 30 days.
    """
    return await certificate_service.get_expiring_certificates(db, days)


@router.get("/expired", response_model=List[VendorCertificateResponse])
async def get_expired_certificates(
    db: AsyncSession = Depends(get_session)
):
    """
    Get all expired certificates
    
    Returns certificates that have already expired.
    """
    return await certificate_service.get_expired_certificates(db)


@router.get("/{certificate_id}", response_model=VendorCertificateResponse)
async def get_certificate(
    certificate_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get a certificate by ID
    
    Returns detailed information about a specific certificate.
    """
    return await certificate_service.get_certificate(db, certificate_id)


@router.put("/{certificate_id}", response_model=VendorCertificateResponse)
async def update_certificate(
    certificate_id: int,
    certificate_data: VendorCertificateUpdate,
    db: AsyncSession = Depends(get_session)
):
    """
    Update a certificate
    
    Updates an existing certificate with new information.
    """
    return await certificate_service.update_certificate(db, certificate_id, certificate_data)


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    certificate_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Delete a certificate
    
    Permanently deletes a certificate from the system.
    """
    await certificate_service.delete_certificate(db, certificate_id)


@router.post("/update-expired-statuses", status_code=status.HTTP_200_OK)
async def update_expired_statuses(
    db: AsyncSession = Depends(get_session)
):
    """
    Update expired certificate statuses
    
    Batch updates all expired certificates to non-compliant status.
    Returns the number of certificates updated.
    """
    count = await certificate_service.update_expired_statuses(db)
    return {"updated_count": count, "message": f"Updated {count} expired certificates"}
