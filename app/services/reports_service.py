"""
Reports Module Service Layer
This file contains all business logic for the Reports module including Applications and Vulnerabilities
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_reports import application_crud, vulnerability_crud
from app.schemas.reports import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    VulnerabilityCreate, VulnerabilityUpdate, VulnerabilityResponse
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# ============= APPLICATION SERVICE =============

class ApplicationService:
    async def create_application(self, db: AsyncSession, *, application_in: ApplicationCreate) -> ApplicationResponse:
        db_app = await application_crud.create(db, obj_in=application_in)
        return ApplicationResponse.from_orm(db_app)

    async def get_application(self, db: AsyncSession, application_id: int) -> Optional[ApplicationResponse]:
        db_app = await application_crud.get(db, id=application_id)
        if not db_app:
            return None
        return ApplicationResponse.from_orm(db_app)

    async def list_applications(self, db: AsyncSession, page: int = 1, size: int = 20) -> Dict[str, Any]:
        apps, total = await application_crud.get_multi(db, page=page, size=size)
        items = [ApplicationResponse.from_orm(a) for a in apps]
        return {"items": items, "total": total, "page": page, "size": size}

    async def update_application(self, db: AsyncSession, application_id: int, application_in: ApplicationUpdate) -> Optional[ApplicationResponse]:
        db_app = await application_crud.get(db, id=application_id)
        if not db_app:
            return None
        updated = await application_crud.update(db, db_obj=db_app, obj_in=application_in)
        return ApplicationResponse.from_orm(updated)

    async def delete_application(self, db: AsyncSession, application_id: int) -> bool:
        return await application_crud.delete(db, id=application_id)


# ============= VULNERABILITY SERVICE =============

class VulnerabilityService:
    async def create_vulnerability(
        self, 
        db: AsyncSession, 
        *, 
        vulnerability_in: VulnerabilityCreate
    ) -> VulnerabilityResponse:
        db_vuln = await vulnerability_crud.create(db, obj_in=vulnerability_in)
        return VulnerabilityResponse.from_orm(db_vuln)

    async def get_vulnerability(
        self, 
        db: AsyncSession, 
        vulnerability_id: int
    ) -> Optional[VulnerabilityResponse]:
        db_vuln = await vulnerability_crud.get(db, id=vulnerability_id)
        if not db_vuln:
            return None
        return VulnerabilityResponse.from_orm(db_vuln)

    async def list_vulnerabilities(
        self, 
        db: AsyncSession, 
        page: int = 1, 
        size: int = 20,
        application_id: Optional[int] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        vulns, total = await vulnerability_crud.get_multi(
            db, 
            page=page, 
            size=size,
            application_id=application_id,
            status=status,
            severity=severity
        )
        items = [VulnerabilityResponse.from_orm(v) for v in vulns]
        return {
            "items": items, 
            "total": total, 
            "page": page, 
            "size": size
        }

    async def update_vulnerability(
        self, 
        db: AsyncSession, 
        vulnerability_id: int, 
        vulnerability_in: VulnerabilityUpdate
    ) -> Optional[VulnerabilityResponse]:
        db_vuln = await vulnerability_crud.get(db, id=vulnerability_id)
        if not db_vuln:
            return None
        updated = await vulnerability_crud.update(db, db_obj=db_vuln, obj_in=vulnerability_in)
        return VulnerabilityResponse.from_orm(updated)

    async def delete_vulnerability(self, db: AsyncSession, vulnerability_id: int) -> bool:
        return await vulnerability_crud.delete(db, id=vulnerability_id)


# Singleton service instances
application_service = ApplicationService()
vulnerability_service = VulnerabilityService()
