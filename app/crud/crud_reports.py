"""
Reports Module CRUD Operations
This file contains all CRUD operations for the Reports module including Applications and Vulnerabilities
"""
from typing import Any, Dict, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.models import Application, Vulnerability
from app.schemas.reports import (
    ApplicationCreate, ApplicationUpdate,
    VulnerabilityCreate, VulnerabilityUpdate
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# ============= APPLICATION CRUD =============

class ApplicationCRUD:
    async def create(self, db: AsyncSession, *, obj_in: ApplicationCreate) -> Application:
        try:
            app_data = obj_in.dict(exclude_unset=True)
            db_app = Application(**app_data)
            db.add(db_app)
            await db.commit()
            await db.refresh(db_app)
            logger.info(f"Created application: {db_app.name} (ID: {db_app.id})")
            return db_app
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating application: {e}")
            raise

    async def get(self, db: AsyncSession, id: int) -> Optional[Application]:
        try:
            result = await db.execute(
                select(Application).options(selectinload(Application.vulnerabilities)).where(Application.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting application {id}: {e}")
            return None

    async def get_multi(self, db: AsyncSession, *, page: int = 1, size: int = 20) -> tuple[List[Application], int]:
        try:
            query = select(Application).order_by(Application.name.asc()).offset((page - 1) * size).limit(size)
            result = await db.execute(query)
            apps = result.scalars().all()

            count_result = await db.execute(select(func.count(Application.id)))
            total = count_result.scalar()

            return apps, total
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            return [], 0

    async def update(self, db: AsyncSession, *, db_obj: Application, obj_in: Union[ApplicationUpdate, Dict[str, Any]]) -> Application:
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            await db.commit()
            await db.refresh(db_obj)
            logger.info(f"Updated application: {db_obj.name} (ID: {db_obj.id})")
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating application {db_obj.id}: {e}")
            raise

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        try:
            result = await db.execute(select(Application).where(Application.id == id))
            app = result.scalar_one_or_none()
            if not app:
                return False
            await db.delete(app)
            await db.commit()
            logger.info(f"Deleted application: {app.name} (ID: {id})")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting application {id}: {e}")
            raise


# ============= VULNERABILITY CRUD =============

class VulnerabilityCRUD:
    async def create(self, db: AsyncSession, *, obj_in: VulnerabilityCreate) -> Vulnerability:
        try:
            vuln_data = obj_in.dict(exclude_unset=True)
            db_vuln = Vulnerability(**vuln_data)
            db.add(db_vuln)
            await db.commit()
            await db.refresh(db_vuln)
            logger.info(f"Created vulnerability: {db_vuln.title} (ID: {db_vuln.id})")
            return db_vuln
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating vulnerability: {e}")
            raise

    async def get(self, db: AsyncSession, id: int) -> Optional[Vulnerability]:
        try:
            result = await db.execute(
                select(Vulnerability)
                .options(
                    selectinload(Vulnerability.application),
                    selectinload(Vulnerability.assigned_to)
                )
                .where(Vulnerability.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting vulnerability {id}: {e}")
            return None

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        page: int = 1, 
        size: int = 20,
        application_id: Optional[int] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None
    ) -> tuple[List[Vulnerability], int]:
        try:
            query = select(Vulnerability)
            
            # Apply filters
            if application_id:
                query = query.where(Vulnerability.application_id == application_id)
            if status:
                query = query.where(Vulnerability.status == status)
            if severity:
                query = query.where(Vulnerability.severity == severity)
            
            # Count total
            count_query = select(func.count(Vulnerability.id))
            if application_id:
                count_query = count_query.where(Vulnerability.application_id == application_id)
            if status:
                count_query = count_query.where(Vulnerability.status == status)
            if severity:
                count_query = count_query.where(Vulnerability.severity == severity)
            
            count_result = await db.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination and ordering
            query = query.order_by(Vulnerability.discovered_date.desc()).offset((page - 1) * size).limit(size)
            result = await db.execute(query)
            vulns = result.scalars().all()

            return vulns, total
        except Exception as e:
            logger.error(f"Error getting vulnerabilities: {e}")
            return [], 0

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Vulnerability, 
        obj_in: Union[VulnerabilityUpdate, Dict[str, Any]]
    ) -> Vulnerability:
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            await db.commit()
            await db.refresh(db_obj)
            logger.info(f"Updated vulnerability: {db_obj.title} (ID: {db_obj.id})")
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating vulnerability {db_obj.id}: {e}")
            raise

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        try:
            result = await db.execute(select(Vulnerability).where(Vulnerability.id == id))
            vuln = result.scalar_one_or_none()
            if not vuln:
                return False
            await db.delete(vuln)
            await db.commit()
            logger.info(f"Deleted vulnerability: {vuln.title} (ID: {id})")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting vulnerability {id}: {e}")
            raise


# Singleton instances
application_crud = ApplicationCRUD()
vulnerability_crud = VulnerabilityCRUD()
