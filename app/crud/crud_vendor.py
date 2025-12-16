from typing import Any, Dict, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, date

from app.models.models import Vendor, VendorComplianceRecord, ComplianceStatus, RiskLevel
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorFilterParams
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class VendorCRUD:
    """CRUD operations for vendors"""

    async def create(self, db: AsyncSession, *, obj_in: VendorCreate, created_by_id: Optional[int] = None) -> Vendor:
        """Create a new vendor"""
        try:
            # Create vendor data dict, excluding non-model fields
            vendor_data = obj_in.dict(exclude={
                'standard', 
                'compliance_requirements',
                'application_name',
                'certificate_type',
                'certificate_issue_date',
                'certificate_expiry_date'
            })
            
            # Create vendor instance
            db_vendor = Vendor(**vendor_data)
            
            db.add(db_vendor)
            await db.commit()
            await db.refresh(db_vendor)
            
            # If initial compliance standard is provided, create compliance record
            if obj_in.standard:
                await self._create_initial_compliance_record(
                    db, vendor=db_vendor, standard=obj_in.standard, created_by_id=created_by_id
                )
            
            logger.info(f"Created vendor: {db_vendor.name} (ID: {db_vendor.id})")
            return db_vendor
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating vendor: {str(e)}")
            raise

    async def get(self, db: AsyncSession, id: int) -> Optional[Vendor]:
        """Get vendor by ID"""
        try:
            result = await db.execute(
                select(Vendor)
                .options(selectinload(Vendor.compliance_records))
                .where(Vendor.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting vendor {id}: {str(e)}")
            return None

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        filters: VendorFilterParams,
        organization_id: Optional[int] = None
    ) -> tuple[List[Vendor], int]:
        """Get multiple vendors with filtering and pagination"""
        try:
            # Import Assignment and ComplianceStandard here to avoid circular imports
            from app.models.models import Assignment, ComplianceStandard
            
            # Base query
            query = select(Vendor).options(selectinload(Vendor.compliance_records))
            count_query = select(func.count(Vendor.id))
            
            # Apply organization filter if provided
            if organization_id:
                query = query.where(Vendor.organization_id == organization_id)
                count_query = count_query.where(Vendor.organization_id == organization_id)
            
            # Filter by compliance standard - vendors must have assignments with this standard
            if filters.standard:
                # Map frontend standard codes to database names
                standard_name_map = {
                    'ISO27001': 'ISO_27001',
                    'PCI_DSS': 'PCIDSS_V4',
                    'SOC2': 'SOC2',
                    'GDPR': 'GDPR',
                    'HIPAA': 'HIPAA',
                    'SOX': 'SOX',
                    'NIST': 'NIST',
                    'COBIT': 'COBIT'
                }
                standard_name = standard_name_map.get(filters.standard.value, filters.standard.value)
                
                # Subquery to find vendors that have assignments with the selected standard
                standard_subquery = (
                    select(Assignment.vendor_id)
                    .join(ComplianceStandard, Assignment.standard_id == ComplianceStandard.id)
                    .where(ComplianceStandard.name == standard_name)
                    .distinct()
                )
                query = query.where(Vendor.id.in_(standard_subquery))
                count_query = count_query.where(Vendor.id.in_(standard_subquery))
            
            # Apply filters
            if filters.search:
                search_pattern = f"%{filters.search}%"
                search_condition = or_(
                    Vendor.name.ilike(search_pattern),
                    Vendor.description.ilike(search_pattern)
                )
                query = query.where(search_condition)
                count_query = count_query.where(search_condition)
            
            if filters.category:
                query = query.where(Vendor.category == filters.category)
                count_query = count_query.where(Vendor.category == filters.category)
            
            if filters.risk_level:
                query = query.where(Vendor.risk_level == filters.risk_level)
                count_query = count_query.where(Vendor.risk_level == filters.risk_level)
            
            if filters.compliance_status:
                query = query.where(Vendor.compliance_status == filters.compliance_status)
                count_query = count_query.where(Vendor.compliance_status == filters.compliance_status)
            
            # Apply sorting
            sort_column = getattr(Vendor, filters.sort_by, Vendor.name)
            if filters.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            # Apply pagination
            offset = (filters.page - 1) * filters.size
            query = query.offset(offset).limit(filters.size)
            
            # Execute queries
            result = await db.execute(query)
            vendors = result.scalars().all()
            
            count_result = await db.execute(count_query)
            total = count_result.scalar()
            
            return list(vendors), total
            
        except Exception as e:
            logger.error(f"Error getting vendors: {str(e)}")
            return [], 0

    async def update(self, db: AsyncSession, *, db_obj: Vendor, obj_in: Union[VendorUpdate, Dict[str, Any]]) -> Vendor:
        """Update vendor"""
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
            
            logger.info(f"Updated vendor: {db_obj.name} (ID: {db_obj.id})")
            return db_obj
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating vendor {db_obj.id}: {str(e)}")
            raise

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """Delete vendor"""
        try:
            result = await db.execute(select(Vendor).where(Vendor.id == id))
            vendor = result.scalar_one_or_none()
            
            if not vendor:
                return False
            
            await db.delete(vendor)
            await db.commit()
            
            logger.info(f"Deleted vendor: {vendor.name} (ID: {id})")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting vendor {id}: {str(e)}")
            raise

    async def get_vendor_stats(self, db: AsyncSession, organization_id: Optional[int] = None) -> Dict[str, int]:
        """Get vendor statistics for dashboard"""
        try:
            base_query = select(Vendor)
            if organization_id:
                base_query = base_query.where(Vendor.organization_id == organization_id)
            
            # Total vendors
            total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
            total_vendors = total_result.scalar()
            
            # Compliant vendors
            compliant_result = await db.execute(
                select(func.count()).select_from(
                    base_query.where(Vendor.compliance_status == ComplianceStatus.COMPLIANT).subquery()
                )
            )
            compliant_vendors = compliant_result.scalar()
            
            # Non-compliant vendors
            non_compliant_result = await db.execute(
                select(func.count()).select_from(
                    base_query.where(Vendor.compliance_status == ComplianceStatus.NON_COMPLIANT).subquery()
                )
            )
            non_compliant_vendors = non_compliant_result.scalar()
            
            # Pending assessment
            pending_result = await db.execute(
                select(func.count()).select_from(
                    base_query.where(Vendor.compliance_status == ComplianceStatus.PENDING).subquery()
                )
            )
            pending_assessment = pending_result.scalar()
            
            # High risk vendors
            high_risk_result = await db.execute(
                select(func.count()).select_from(
                    base_query.where(
                        or_(Vendor.risk_level == RiskLevel.HIGH, Vendor.risk_level == RiskLevel.CRITICAL)
                    ).subquery()
                )
            )
            high_risk_vendors = high_risk_result.scalar()
            
            # Expiring certificates (next 30 days)
            future_date = date.today().replace(day=date.today().day + 30) if date.today().day <= 28 else date.today().replace(month=date.today().month + 1, day=1)
            
            expiring_result = await db.execute(
                select(func.count(VendorComplianceRecord.id)).where(
                    and_(
                        VendorComplianceRecord.expiry_date.is_not(None),
                        VendorComplianceRecord.expiry_date <= future_date,
                        VendorComplianceRecord.expiry_date > date.today()
                    )
                )
            )
            expiring_certificates = expiring_result.scalar()
            
            return {
                "total_vendors": total_vendors or 0,
                "compliant_vendors": compliant_vendors or 0,
                "non_compliant_vendors": non_compliant_vendors or 0,
                "pending_assessment": pending_assessment or 0,
                "high_risk_vendors": high_risk_vendors or 0,
                "expiring_certificates": expiring_certificates or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting vendor stats: {str(e)}")
            return {
                "total_vendors": 0,
                "compliant_vendors": 0,
                "non_compliant_vendors": 0,
                "pending_assessment": 0,
                "high_risk_vendors": 0,
                "expiring_certificates": 0
            }

    async def get_risk_distribution(self, db: AsyncSession, organization_id: Optional[int] = None) -> Dict[str, int]:
        """Get vendor risk level distribution"""
        try:
            base_query = select(Vendor.risk_level, func.count(Vendor.id)).group_by(Vendor.risk_level)
            if organization_id:
                base_query = base_query.where(Vendor.organization_id == organization_id)
            
            result = await db.execute(base_query)
            distribution = {level.value: 0 for level in RiskLevel}
            
            for risk_level, count in result.fetchall():
                distribution[risk_level] = count
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting risk distribution: {str(e)}")
            return {level.value: 0 for level in RiskLevel}

    async def get_recent_vendors(
        self, 
        db: AsyncSession, 
        limit: int = 5, 
        organization_id: Optional[int] = None
    ) -> List[Vendor]:
        """Get recently created vendors"""
        try:
            query = select(Vendor).order_by(Vendor.created_at.desc()).limit(limit)
            
            if organization_id:
                query = query.where(Vendor.organization_id == organization_id)
            
            result = await db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting recent vendors: {str(e)}")
            return []

    async def _create_initial_compliance_record(
        self, 
        db: AsyncSession, 
        vendor: Vendor, 
        standard: str,
        created_by_id: Optional[int] = None
    ):
        """Create initial compliance record for vendor"""
        try:
            compliance_record = VendorComplianceRecord(
                vendor_id=vendor.id,
                compliance_area=standard,
                status=ComplianceStatus.PENDING,
                assessment_date=date.today(),
                assessor_id=created_by_id,
                notes=f"Initial compliance record for {standard} standard"
            )
            
            db.add(compliance_record)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error creating initial compliance record: {str(e)}")
            raise

    async def bulk_update(
        self, 
        db: AsyncSession, 
        vendor_ids: List[int], 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bulk update multiple vendors"""
        try:
            success_count = 0
            failed_count = 0
            errors = []
            
            for vendor_id in vendor_ids:
                try:
                    vendor = await self.get(db, vendor_id)
                    if vendor:
                        await self.update(db, db_obj=vendor, obj_in=updates)
                        success_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            "vendor_id": vendor_id,
                            "error": "Vendor not found"
                        })
                except Exception as e:
                    failed_count += 1
                    errors.append({
                        "vendor_id": vendor_id,
                        "error": str(e)
                    })
            
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in bulk update: {str(e)}")
            raise


# Create instance
vendor_crud = VendorCRUD()