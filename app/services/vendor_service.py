from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.crud.crud_vendor import vendor_crud
from app.crud.crud_certificate import certificate_crud
from app.schemas.vendor import (
    VendorCreate, VendorUpdate, VendorResponse, VendorListResponse,
    VendorFilterParams, VendorStatsResponse, VendorDashboardResponse,
    VendorRiskDistribution, VendorComplianceDistribution, 
    StandardOptionsResponse, StandardOption, ComplianceStandardEnum
)
from app.schemas.certificate import VendorCertificateCreate
from app.models.models import Vendor, RiskLevel, ComplianceStatus, Application, ApplicationType
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class VendorService:
    """Business logic for vendor management"""

    def __init__(self):
        self.crud = vendor_crud

    async def create_vendor(
        self, 
        db: AsyncSession, 
        vendor_data: VendorCreate,
        current_user_id: Optional[int] = None
    ) -> VendorResponse:
        """Create a new vendor with business logic validation"""
        try:
            # Business logic validations
            await self._validate_vendor_creation(db, vendor_data)
            
            # Create vendor
            vendor = await self.crud.create(
                db, 
                obj_in=vendor_data, 
                created_by_id=current_user_id
            )
            
            # Create associated application if provided
            application_id = None
            if vendor_data.application_name:
                application_id = await self._create_application(
                    db, 
                    vendor_data.application_name, 
                    current_user_id
                )
            
            # Create certificate if provided
            if vendor_data.certificate_type and vendor_data.certificate_issue_date and vendor_data.certificate_expiry_date:
                await self._create_certificate(
                    db,
                    vendor.id,
                    application_id,
                    vendor_data.certificate_type,
                    vendor_data.certificate_issue_date,
                    vendor_data.certificate_expiry_date
                )
            
            # Convert to response schema
            return await self._vendor_to_response(db, vendor)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in create_vendor service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create vendor"
            )

    async def get_vendor(self, db: AsyncSession, vendor_id: int) -> VendorResponse:
        """Get vendor by ID"""
        vendor = await self.crud.get(db, vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        return await self._vendor_to_response(db, vendor)

    async def get_vendors(
        self, 
        db: AsyncSession, 
        filters: VendorFilterParams,
        organization_id: Optional[int] = None
    ) -> VendorListResponse:
        """Get filtered list of vendors"""
        try:
            vendors, total = await self.crud.get_multi(
                db, 
                filters=filters, 
                organization_id=organization_id
            )
            
            # Convert to response format
            vendor_responses = []
            for vendor in vendors:
                vendor_response = await self._vendor_to_response(db, vendor)
                vendor_responses.append(vendor_response)
            
            pages = (total + filters.size - 1) // filters.size
            
            return VendorListResponse(
                vendors=vendor_responses,
                total=total,
                page=filters.page,
                size=filters.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error in get_vendors service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve vendors"
            )

    async def update_vendor(
        self, 
        db: AsyncSession, 
        vendor_id: int, 
        vendor_data: VendorUpdate,
        current_user_id: Optional[int] = None
    ) -> VendorResponse:
        """Update vendor"""
        try:
            vendor = await self.crud.get(db, vendor_id)
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor not found"
                )
            
            # Business logic validations
            await self._validate_vendor_update(db, vendor_id, vendor_data)
            
            # Update vendor
            updated_vendor = await self.crud.update(
                db, 
                db_obj=vendor, 
                obj_in=vendor_data
            )
            
            return await self._vendor_to_response(db, updated_vendor)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_vendor service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update vendor"
            )

    async def delete_vendor(self, db: AsyncSession, vendor_id: int) -> bool:
        """Delete vendor"""
        try:
            success = await self.crud.delete(db, id=vendor_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor not found"
                )
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in delete_vendor service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete vendor"
            )

    async def get_vendor_dashboard(
        self, 
        db: AsyncSession, 
        organization_id: Optional[int] = None
    ) -> VendorDashboardResponse:
        """Get comprehensive vendor dashboard data"""
        try:
            # Get vendor statistics
            stats_data = await self.crud.get_vendor_stats(db, organization_id)
            stats = VendorStatsResponse(**stats_data)
            
            # Get risk distribution
            risk_dist_data = await self.crud.get_risk_distribution(db, organization_id)
            risk_distribution = VendorRiskDistribution(**risk_dist_data)
            
            # Get compliance distribution
            compliance_dist_data = await self._get_compliance_distribution(db, organization_id)
            compliance_distribution = VendorComplianceDistribution(**compliance_dist_data)
            
            # Get recent vendors
            recent_vendors_list = await self.crud.get_recent_vendors(db, 5, organization_id)
            recent_vendors = []
            for vendor in recent_vendors_list:
                vendor_response = await self._vendor_to_response(db, vendor)
                recent_vendors.append(vendor_response)
            
            # TODO: Get expiring certificates
            expiring_certificates = []
            
            return VendorDashboardResponse(
                stats=stats,
                risk_distribution=risk_distribution,
                compliance_distribution=compliance_distribution,
                recent_vendors=recent_vendors,
                expiring_certificates=expiring_certificates
            )
            
        except Exception as e:
            logger.error(f"Error in get_vendor_dashboard service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve dashboard data"
            )

    async def get_standard_options(self) -> StandardOptionsResponse:
        """Get available compliance standards for frontend dropdown"""
        standards = []
        
        standard_mappings = {
            ComplianceStandardEnum.ISO27001: {
                "label": "ISO 27001 - Information Security Management",
                "description": "International standard for information security management systems"
            },
            ComplianceStandardEnum.PCI_DSS: {
                "label": "PCI DSS - Payment Card Industry Data Security Standard",
                "description": "Security standard for organizations that handle credit cards"
            },
            ComplianceStandardEnum.SOX: {
                "label": "SOX - Sarbanes-Oxley Act",
                "description": "US federal law for financial reporting and corporate governance"
            },
            ComplianceStandardEnum.GDPR: {
                "label": "GDPR - General Data Protection Regulation",
                "description": "EU regulation for data protection and privacy"
            },
            ComplianceStandardEnum.HIPAA: {
                "label": "HIPAA - Health Insurance Portability and Accountability Act",
                "description": "US legislation for healthcare data protection"
            },
            ComplianceStandardEnum.SOC2: {
                "label": "SOC 2 - Service Organization Control 2",
                "description": "Auditing procedure for service providers storing customer data"
            },
            ComplianceStandardEnum.NIST: {
                "label": "NIST Cybersecurity Framework",
                "description": "Framework for improving cybersecurity risk management"
            },
            ComplianceStandardEnum.COBIT: {
                "label": "COBIT - Control Objectives for Information and Related Technologies",
                "description": "Framework for governance and management of enterprise IT"
            }
        }
        
        for standard_enum in ComplianceStandardEnum:
            mapping = standard_mappings.get(standard_enum, {
                "label": standard_enum.value,
                "description": None
            })
            
            standards.append(StandardOption(
                value=standard_enum.value,
                label=mapping["label"],
                description=mapping["description"]
            ))
        
        return StandardOptionsResponse(standards=standards)

    async def _validate_vendor_creation(self, db: AsyncSession, vendor_data: VendorCreate):
        """Validate vendor creation business rules"""
        # Check for duplicate vendor names
        filters = VendorFilterParams(search=vendor_data.name, page=1, size=1)
        existing_vendors, _ = await self.crud.get_multi(db, filters=filters)
        
        for vendor in existing_vendors:
            if vendor.name.lower() == vendor_data.name.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Vendor with name '{vendor_data.name}' already exists"
                )
        
        # Validate contract dates
        if vendor_data.contract_start_date and vendor_data.contract_end_date:
            if vendor_data.contract_start_date >= vendor_data.contract_end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contract start date must be before end date"
                )

    async def _validate_vendor_update(self, db: AsyncSession, vendor_id: int, vendor_data: VendorUpdate):
        """Validate vendor update business rules"""
        # Check for duplicate names (excluding current vendor)
        if vendor_data.name:
            filters = VendorFilterParams(search=vendor_data.name, page=1, size=10)
            existing_vendors, _ = await self.crud.get_multi(db, filters=filters)
            
            for vendor in existing_vendors:
                if vendor.id != vendor_id and vendor.name.lower() == vendor_data.name.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Vendor with name '{vendor_data.name}' already exists"
                    )
        
        # Validate contract dates
        if vendor_data.contract_start_date and vendor_data.contract_end_date:
            if vendor_data.contract_start_date >= vendor_data.contract_end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contract start date must be before end date"
                )

    async def _vendor_to_response(self, db: AsyncSession, vendor: Vendor) -> VendorResponse:
        """Convert vendor model to response schema"""
        try:
            logger.debug(f"Converting vendor {vendor.id} to response")
            
            # Safely access relationships without triggering async loading
            compliance_records_count = 0
            vulnerabilities_count = 0
            
            try:
                # Check if compliance_records is loaded
                if hasattr(vendor, 'compliance_records'):
                    compliance_records = vendor.compliance_records
                    if compliance_records is not None:
                        compliance_records_count = len(compliance_records)
            except Exception as e:
                logger.warning(f"Could not access compliance_records for vendor {vendor.id}: {e}")
                compliance_records_count = 0
                
            try:
                # Check if vulnerabilities is loaded
                if hasattr(vendor, 'vulnerabilities'):
                    vulnerabilities = vendor.vulnerabilities  
                    if vulnerabilities is not None:
                        vulnerabilities_count = len(vulnerabilities)
            except Exception as e:
                logger.warning(f"Could not access vulnerabilities for vendor {vendor.id}: {e}")
                vulnerabilities_count = 0
            
            return VendorResponse(
                id=vendor.id,
                name=vendor.name,
                description=vendor.description,
                category=vendor.category,
                contact_email=vendor.contact_email,
                contact_phone=vendor.contact_phone,
                website=vendor.website,
                risk_level=vendor.risk_level,
                compliance_status=vendor.compliance_status,
                last_risk_assessment=vendor.last_risk_assessment,
                next_risk_assessment=vendor.next_risk_assessment,
                contract_start_date=vendor.contract_start_date,
                contract_end_date=vendor.contract_end_date,
                contract_value=vendor.contract_value,
                created_at=vendor.created_at,
                updated_at=vendor.updated_at,
                # Compliance metrics
                compliance_rate=float(vendor.compliance_rate) if vendor.compliance_rate else None,
                compliant_controls=vendor.compliant_controls,
                non_compliant_controls=vendor.non_compliant_controls,
                last_compliance_check=vendor.last_compliance_check,
                # Related counts
                compliance_records_count=compliance_records_count,
                active_vulnerabilities_count=vulnerabilities_count
            )
        except Exception as e:
            logger.error(f"Error converting vendor to response: {str(e)}")
            logger.exception(e)
            raise

    async def _get_compliance_distribution(self, db: AsyncSession, organization_id: Optional[int] = None) -> Dict[str, int]:
        """Get compliance status distribution"""
        try:
            # This is a simplified version - you might want to implement this in CRUD
            stats_data = await self.crud.get_vendor_stats(db, organization_id)
            
            return {
                "compliant": stats_data.get("compliant_vendors", 0),
                "non_compliant": stats_data.get("non_compliant_vendors", 0),
                "pending": stats_data.get("pending_assessment", 0),
                "exception": 0,  # TODO: Implement exception tracking
                "not_applicable": 0  # TODO: Implement not applicable tracking
            }
        except Exception as e:
            logger.error(f"Error getting compliance distribution: {str(e)}")
            return {"compliant": 0, "non_compliant": 0, "pending": 0, "exception": 0, "not_applicable": 0}
    
    async def _create_application(
        self, 
        db: AsyncSession, 
        application_name: str,
        owner_id: Optional[int] = None
    ) -> Optional[int]:
        """Create an application and return its ID"""
        try:
            from sqlalchemy import insert
            
            application_data = {
                "name": application_name,
                "application_type": ApplicationType.WEB_APPLICATION,  # Default type
                "risk_level": RiskLevel.MEDIUM,  # Default risk level
                "owner_id": owner_id
            }
            
            stmt = insert(Application).values(**application_data).returning(Application.id)
            result = await db.execute(stmt)
            await db.commit()
            
            app_id = result.scalar_one()
            logger.info(f"Created application: {application_name} with ID: {app_id}")
            return app_id
            
        except Exception as e:
            logger.error(f"Error creating application: {str(e)}")
            await db.rollback()
            return None
    
    async def _create_certificate(
        self,
        db: AsyncSession,
        vendor_id: int,
        application_id: Optional[int],
        certificate_type: str,
        issue_date,
        expiry_date
    ) -> None:
        """Create a vendor certificate"""
        try:
            certificate_data = VendorCertificateCreate(
                vendor_id=vendor_id,
                application_id=application_id,
                certificate_type=certificate_type,
                issue_date=issue_date,
                expiry_date=expiry_date,
                status=ComplianceStatus.COMPLIANT
            )
            
            await certificate_crud.create(db, obj_in=certificate_data)
            logger.info(f"Created certificate for vendor {vendor_id}: {certificate_type}")
            
        except Exception as e:
            logger.error(f"Error creating certificate: {str(e)}")
            # Don't rollback - certificate is optional


# Create service instance
vendor_service = VendorService()