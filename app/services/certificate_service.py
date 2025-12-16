from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.crud.crud_certificate import certificate_crud
from app.schemas.certificate import VendorCertificateCreate, VendorCertificateUpdate, VendorCertificateResponse
from app.models.models import VendorCertificate


class CertificateService:
    """Service for managing vendor certificates"""
    
    async def create_certificate(
        self, 
        db: AsyncSession, 
        certificate_data: VendorCertificateCreate
    ) -> VendorCertificateResponse:
        """Create a new certificate"""
        certificate = await certificate_crud.create(db, obj_in=certificate_data)
        return VendorCertificateResponse.from_orm(certificate)
    
    async def get_certificate(
        self, 
        db: AsyncSession, 
        certificate_id: int
    ) -> VendorCertificateResponse:
        """Get certificate by ID"""
        certificate = await certificate_crud.get(db, id=certificate_id)
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Certificate with id {certificate_id} not found"
            )
        return VendorCertificateResponse.from_orm(certificate)
    
    async def get_vendor_certificates(
        self, 
        db: AsyncSession, 
        vendor_id: int,
        active_only: bool = False
    ) -> List[VendorCertificateResponse]:
        """Get all certificates for a vendor"""
        certificates = await certificate_crud.get_by_vendor(db, vendor_id, active_only)
        return [VendorCertificateResponse.from_orm(cert) for cert in certificates]
    
    async def get_application_certificates(
        self, 
        db: AsyncSession, 
        application_id: int
    ) -> List[VendorCertificateResponse]:
        """Get all certificates for an application"""
        certificates = await certificate_crud.get_by_application(db, application_id)
        return [VendorCertificateResponse.from_orm(cert) for cert in certificates]
    
    async def get_expiring_certificates(
        self, 
        db: AsyncSession, 
        days: int = 30
    ) -> List[VendorCertificateResponse]:
        """Get certificates expiring within specified days"""
        certificates = await certificate_crud.get_expiring_soon(db, days)
        return [VendorCertificateResponse.from_orm(cert) for cert in certificates]
    
    async def get_expired_certificates(
        self, 
        db: AsyncSession
    ) -> List[VendorCertificateResponse]:
        """Get all expired certificates"""
        certificates = await certificate_crud.get_expired(db)
        return [VendorCertificateResponse.from_orm(cert) for cert in certificates]
    
    async def update_certificate(
        self, 
        db: AsyncSession, 
        certificate_id: int,
        certificate_data: VendorCertificateUpdate
    ) -> VendorCertificateResponse:
        """Update a certificate"""
        certificate = await certificate_crud.get(db, id=certificate_id)
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Certificate with id {certificate_id} not found"
            )
        
        updated_certificate = await certificate_crud.update(
            db, 
            db_obj=certificate, 
            obj_in=certificate_data
        )
        return VendorCertificateResponse.from_orm(updated_certificate)
    
    async def delete_certificate(
        self, 
        db: AsyncSession, 
        certificate_id: int
    ) -> None:
        """Delete a certificate"""
        certificate = await certificate_crud.get(db, id=certificate_id)
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Certificate with id {certificate_id} not found"
            )
        
        await certificate_crud.remove(db, id=certificate_id)
    
    async def update_expired_statuses(self, db: AsyncSession) -> int:
        """Update status of expired certificates"""
        return await certificate_crud.update_expired_statuses(db)


certificate_service = CertificateService()
