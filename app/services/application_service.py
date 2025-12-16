"""Application service for business logic"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.crud.crud_application import application as crud_application
from app.crud.crud_vulnerability import vulnerability as crud_vulnerability
from app.models.models import ApplicationType, RiskLevel, VulnerabilityStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationFilterParams,
    ApplicationStatistics
)
from app.schemas.vulnerability import VulnerabilityCreate
from app.utils.logger import logger


class ApplicationService:
    """Service for application operations"""
    
    async def create_application(
        self,
        db: AsyncSession,
        *,
        application_in: ApplicationCreate
    ) -> ApplicationResponse:
        """
        Create a new application with optional vulnerabilities
        
        Args:
            db: Database session
            application_in: Application data with optional vulnerabilities
            
        Returns:
            Created application response
        """
        try:
            # Convert frontend type string to ApplicationType enum
            app_type = ApplicationType(application_in.type.value)
            risk_level = RiskLevel(application_in.risk_level.value) if application_in.risk_level else RiskLevel.MEDIUM
            
            # Prepare application data (exclude vulnerabilities for model creation)
            app_data = {
                "name": application_in.name,
                "description": application_in.description,
                "application_type": app_type,
                "owner": application_in.owner,
                "vendor_name": application_in.vendor,
                "version": application_in.version,
                "url": application_in.url,
                "risk_level": risk_level,
                "business_criticality": application_in.business_criticality
            }
            
            # Create application
            application = await crud_application.create(db=db, obj_in=app_data)
            
            # Create vulnerabilities if provided
            vuln_count = 0
            if application_in.vulnerabilities:
                for vuln_data in application_in.vulnerabilities:
                    # Map category to severity enum
                    severity_map = {
                        "critical": RiskLevel.CRITICAL,
                        "high": RiskLevel.HIGH,
                        "medium": RiskLevel.MEDIUM,
                        "low": RiskLevel.LOW
                    }
                    severity = severity_map.get(vuln_data.category.lower(), RiskLevel.MEDIUM)
                    
                    # Create vulnerability linked to this application
                    vuln_create = VulnerabilityCreate(
                        title=vuln_data.name,
                        description=vuln_data.description or "",
                        severity=severity,
                        application_id=application.id,
                        remarks=f"Created with application {application.name}"
                    )
                    
                    await crud_vulnerability.create(db=db, obj_in=vuln_create)
                    vuln_count += 1
            
            logger.info(f"Created application: {application.id} - {application.name} with {vuln_count} vulnerabilities")
            
            return ApplicationResponse.from_orm_with_vuln_count(application, vuln_count)
            
        except ValueError as e:
            logger.error(f"Invalid enum value: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid application type or risk level: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating application: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create application: {str(e)}"
            )
    
    async def get_applications(
        self,
        db: AsyncSession,
        *,
        filters: ApplicationFilterParams
    ) -> ApplicationListResponse:
        """
        Get applications with filtering and pagination
        
        Args:
            db: Database session
            filters: Filter parameters
            
        Returns:
            Paginated application list
        """
        try:
            # Get applications with filters
            applications, total = await crud_application.get_multi_with_filters(
                db=db,
                filters=filters
            )
            
            # Convert to response models with vulnerability counts
            items = []
            for app in applications:
                vuln_count = await crud_application.get_vulnerability_count(
                    db=db,
                    application_id=app.id
                )
                items.append(ApplicationResponse.from_orm_with_vuln_count(app, vuln_count))
            
            # Calculate pages
            pages = (total + filters.size - 1) // filters.size
            
            return ApplicationListResponse(
                items=items,
                total=total,
                page=filters.page,
                size=filters.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error getting applications: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get applications: {str(e)}"
            )
    
    async def get_application_by_id(
        self,
        db: AsyncSession,
        *,
        application_id: int
    ) -> ApplicationResponse:
        """
        Get application by ID
        
        Args:
            db: Database session
            application_id: Application ID
            
        Returns:
            Application response
            
        Raises:
            HTTPException: If application not found
        """
        application = await crud_application.get_with_vulnerabilities(
            db=db,
            id=application_id
        )
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID {application_id} not found"
            )
        
        vuln_count = len(application.vulnerabilities) if application.vulnerabilities else 0
        
        return ApplicationResponse.from_orm_with_vuln_count(application, vuln_count)
    
    async def update_application(
        self,
        db: AsyncSession,
        *,
        application_id: int,
        application_in: ApplicationUpdate
    ) -> ApplicationResponse:
        """
        Update application
        
        Args:
            db: Database session
            application_id: Application ID
            application_in: Updated data
            
        Returns:
            Updated application response
            
        Raises:
            HTTPException: If application not found
        """
        # Get existing application
        application = await crud_application.get(db=db, id=application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID {application_id} not found"
            )
        
        try:
            # Prepare update data
            update_data = application_in.model_dump(exclude_unset=True)
            
            # Handle enum conversions
            if "type" in update_data:
                update_data["application_type"] = ApplicationType(update_data.pop("type").value)
            if "risk_level" in update_data and update_data["risk_level"]:
                update_data["risk_level"] = RiskLevel(update_data["risk_level"].value)
            if "vendor" in update_data:
                update_data["vendor_name"] = update_data.pop("vendor")
            
            # Update application
            application = await crud_application.update(
                db=db,
                db_obj=application,
                obj_in=update_data
            )
            
            # Get vulnerability count
            vuln_count = await crud_application.get_vulnerability_count(
                db=db,
                application_id=application_id
            )
            
            logger.info(f"Updated application: {application_id}")
            
            return ApplicationResponse.from_orm_with_vuln_count(application, vuln_count)
            
        except ValueError as e:
            logger.error(f"Invalid enum value: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid application type or risk level: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error updating application {application_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update application: {str(e)}"
            )
    
    async def delete_application(
        self,
        db: AsyncSession,
        *,
        application_id: int
    ) -> bool:
        """
        Delete application
        
        Args:
            db: Database session
            application_id: Application ID
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException: If application not found
        """
        application = await crud_application.get(db=db, id=application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID {application_id} not found"
            )
        
        try:
            await crud_application.remove(db=db, id=application_id)
            logger.info(f"Deleted application: {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting application {application_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete application: {str(e)}"
            )
    
    async def get_statistics(
        self,
        db: AsyncSession
    ) -> ApplicationStatistics:
        """
        Get application statistics
        
        Args:
            db: Database session
            
        Returns:
            Application statistics
        """
        try:
            statistics = await crud_application.get_statistics(db=db)
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting application statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get application statistics: {str(e)}"
            )


# Create service instance
application_service = ApplicationService()
