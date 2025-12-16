"""CRUD operations for applications"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.models import Application, ApplicationType, RiskLevel, Vulnerability
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationFilterParams,
    ApplicationStatistics
)


class CRUDApplication(CRUDBase[Application, ApplicationCreate, ApplicationUpdate]):
    """CRUD operations for Application model"""
    
    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: ApplicationFilterParams
    ) -> Tuple[List[Application], int]:
        """
        Get applications with filtering and pagination
        
        Args:
            db: Database session
            filters: Filter parameters
            
        Returns:
            Tuple of (applications list, total count)
        """
        # Build base query
        query = select(Application)
        
        # Apply filters
        conditions = []
        
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Application.name.ilike(search_term),
                    Application.description.ilike(search_term),
                    Application.owner.ilike(search_term)
                )
            )
        
        if filters.type:
            conditions.append(Application.application_type == filters.type.value)
        
        if filters.risk_level:
            conditions.append(Application.risk_level == filters.risk_level.value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(Application)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(Application.created_at.desc())
        query = query.offset((filters.page - 1) * filters.size).limit(filters.size)
        
        # Execute query
        result = await db.execute(query)
        applications = result.scalars().all()
        
        return list(applications), total
    
    async def get_with_vulnerabilities(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[Application]:
        """
        Get application by ID with vulnerabilities loaded
        
        Args:
            db: Database session
            id: Application ID
            
        Returns:
            Application with vulnerabilities or None
        """
        query = select(Application).options(
            selectinload(Application.vulnerabilities)
        ).where(Application.id == id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_vulnerability_count(
        self,
        db: AsyncSession,
        *,
        application_id: int
    ) -> int:
        """
        Get count of vulnerabilities for an application
        
        Args:
            db: Database session
            application_id: Application ID
            
        Returns:
            Count of vulnerabilities
        """
        query = select(func.count()).select_from(Vulnerability).where(
            Vulnerability.application_id == application_id
        )
        
        result = await db.execute(query)
        return result.scalar_one()
    
    async def get_statistics(
        self,
        db: AsyncSession
    ) -> ApplicationStatistics:
        """
        Get application statistics
        
        Args:
            db: Database session
            
        Returns:
            ApplicationStatistics with counts
        """
        # Total count
        total_query = select(func.count()).select_from(Application)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()
        
        # Count by type
        type_query = select(
            Application.application_type,
            func.count(Application.id).label('count')
        ).group_by(Application.application_type)
        
        type_result = await db.execute(type_query)
        by_type = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in type_result.all()}
        
        # Count by risk level
        risk_query = select(
            Application.risk_level,
            func.count(Application.id).label('count')
        ).group_by(Application.risk_level)
        
        risk_result = await db.execute(risk_query)
        by_risk_level = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in risk_result.all()}
        
        # Count applications with/without vulnerabilities
        with_vuln_query = select(func.count(func.distinct(Vulnerability.application_id))).select_from(Vulnerability).where(
            Vulnerability.application_id.isnot(None)
        )
        with_vuln_result = await db.execute(with_vuln_query)
        with_vulnerabilities = with_vuln_result.scalar_one()
        
        without_vulnerabilities = total - with_vulnerabilities
        
        return ApplicationStatistics(
            total=total,
            by_type=by_type,
            by_risk_level=by_risk_level,
            with_vulnerabilities=with_vulnerabilities,
            without_vulnerabilities=without_vulnerabilities
        )


# Create instance
application = CRUDApplication(Application)
