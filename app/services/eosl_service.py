"""EOSL (End of Service Life) Service"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_, or_, desc
from collections import defaultdict

from app.models.models import EOSLRecord, RiskLevel, Application, User
from app.schemas.eosl import (
    EOSLAssetCreate, EOSLAssetUpdate, EOSLAssetResponse,
    EOSLAssetListResponse, TopNonCompliantAsset, ComplianceMonthData,
    EOSLSummary, EOSLDashboardResponse, EOSLType
)

logger = logging.getLogger(__name__)


class EOSLService:
    """Service for EOSL asset operations"""
    
    @staticmethod
    async def create_asset(db: AsyncSession, asset_data: EOSLAssetCreate, user_id: Optional[int] = None) -> EOSLAssetResponse:
        """Create a new EOSL asset"""
        try:
            # Map frontend fields to database fields
            db_asset = EOSLRecord(
                product_name=asset_data.asset_name,
                vendor_name=asset_data.owner,  # Using owner as vendor_name
                category=asset_data.asset_type,
                risk_level=RiskLevel.HIGH if asset_data.eosl_type == EOSLType.EOL else RiskLevel.MEDIUM,
                end_of_support_date=asset_data.eosl_date if asset_data.eosl_type == EOSLType.EOS else None,
                end_of_sale_date=asset_data.eosl_date if asset_data.eosl_type == EOSLType.EOL else None,
                business_impact=asset_data.remark,
                owner_id=user_id
            )
            
            db.add(db_asset)
            await db.commit()
            await db.refresh(db_asset)
            
            return await EOSLService._map_to_response(db_asset)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating EOSL asset: {str(e)}")
            raise
    
    @staticmethod
    async def get_assets(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        eosl_type: Optional[str] = None,
        owner: Optional[str] = None
    ) -> EOSLAssetListResponse:
        """Get paginated list of EOSL assets"""
        try:
            query = select(EOSLRecord)
            
            # Apply filters
            if eosl_type:
                if eosl_type.upper() == "EOS":
                    query = query.where(EOSLRecord.end_of_support_date.isnot(None))
                elif eosl_type.upper() == "EOL":
                    query = query.where(EOSLRecord.end_of_sale_date.isnot(None))
            
            if owner:
                query = query.where(EOSLRecord.vendor_name == owner)
            
            # Get total count
            count_query = select(func.count()).select_from(EOSLRecord)
            if eosl_type or owner:
                count_query = count_query.where(*query.whereclause.clauses)
            
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Get paginated results
            query = query.order_by(desc(EOSLRecord.created_at)).offset(skip).limit(limit)
            result = await db.execute(query)
            assets = result.scalars().all()
            
            # Map to response
            response_items = [await EOSLService._map_to_response(asset) for asset in assets]
            
            pages = (total + limit - 1) // limit if limit > 0 else 0
            
            return EOSLAssetListResponse(
                items=response_items,
                total=total,
                page=(skip // limit) + 1 if limit > 0 else 1,
                size=limit,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error fetching EOSL assets: {str(e)}")
            raise
    
    @staticmethod
    async def get_asset_by_id(db: AsyncSession, asset_id: int) -> Optional[EOSLAssetResponse]:
        """Get EOSL asset by ID"""
        try:
            query = select(EOSLRecord).where(EOSLRecord.id == asset_id)
            result = await db.execute(query)
            asset = result.scalar_one_or_none()
            
            if not asset:
                return None
            
            return await EOSLService._map_to_response(asset)
            
        except Exception as e:
            logger.error(f"Error fetching EOSL asset {asset_id}: {str(e)}")
            raise
    
    @staticmethod
    async def update_asset(
        db: AsyncSession,
        asset_id: int,
        asset_data: EOSLAssetUpdate
    ) -> Optional[EOSLAssetResponse]:
        """Update EOSL asset"""
        try:
            query = select(EOSLRecord).where(EOSLRecord.id == asset_id)
            result = await db.execute(query)
            asset = result.scalar_one_or_none()
            
            if not asset:
                return None
            
            # Update fields
            update_data = asset_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == "asset_name":
                    asset.product_name = value
                elif field == "owner":
                    asset.vendor_name = value
                elif field == "asset_type":
                    asset.category = value
                elif field == "eosl_type":
                    if value == EOSLType.EOS:
                        asset.risk_level = RiskLevel.MEDIUM
                    else:
                        asset.risk_level = RiskLevel.HIGH
                elif field == "eosl_date":
                    if asset.end_of_support_date:
                        asset.end_of_support_date = value
                    if asset.end_of_sale_date:
                        asset.end_of_sale_date = value
                elif field == "remark":
                    asset.business_impact = value
            
            await db.commit()
            await db.refresh(asset)
            
            return await EOSLService._map_to_response(asset)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating EOSL asset {asset_id}: {str(e)}")
            raise
    
    @staticmethod
    async def delete_asset(db: AsyncSession, asset_id: int) -> bool:
        """Delete EOSL asset"""
        try:
            query = select(EOSLRecord).where(EOSLRecord.id == asset_id)
            result = await db.execute(query)
            asset = result.scalar_one_or_none()
            
            if not asset:
                return False
            
            await db.delete(asset)
            await db.commit()
            
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting EOSL asset {asset_id}: {str(e)}")
            raise
    
    @staticmethod
    async def get_dashboard_data(db: AsyncSession, year: Optional[int] = None) -> EOSLDashboardResponse:
        """Get complete EOSL dashboard data"""
        try:
            if year is None:
                year = datetime.now().year
            
            # Get all assets
            assets_query = select(EOSLRecord).order_by(
                EOSLRecord.end_of_support_date,
                EOSLRecord.end_of_sale_date
            )
            result = await db.execute(assets_query)
            all_assets = result.scalars().all()
            
            # Map to response
            asset_responses = [await EOSLService._map_to_response(asset) for asset in all_assets]
            
            # Calculate top non-compliant assets by type
            type_counts = defaultdict(int)
            for asset in all_assets:
                if asset.category:
                    type_counts[asset.category] += 1
            
            top_non_compliant = [
                TopNonCompliantAsset(name=asset_type, count=count)
                for asset_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:4]
            ]
            
            # Calculate compliance by year (mock data for now - can be enhanced)
            compliance_by_year = await EOSLService._generate_compliance_by_year(db, year)
            
            # Calculate summary
            today = date.today()
            eos_count = sum(1 for a in all_assets if a.end_of_support_date)
            eol_count = sum(1 for a in all_assets if a.end_of_sale_date)
            
            expiring_soon = sum(
                1 for a in all_assets
                if (a.end_of_support_date and a.end_of_support_date > today and a.end_of_support_date <= today + timedelta(days=30))
                or (a.end_of_sale_date and a.end_of_sale_date > today and a.end_of_sale_date <= today + timedelta(days=30))
            )
            
            expired = sum(
                1 for a in all_assets
                if (a.end_of_support_date and a.end_of_support_date < today)
                or (a.end_of_sale_date and a.end_of_sale_date < today)
            )
            
            summary = EOSLSummary(
                eosCount=eos_count,
                eolCount=eol_count,
                totalAssets=len(all_assets),
                expiringSoon=expiring_soon,
                expired=expired
            )
            
            return EOSLDashboardResponse(
                assets=asset_responses,
                topNonCompliantAssets=top_non_compliant,
                complianceByYear=compliance_by_year,
                summary=summary,
                currentDateTime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                currentUser="System"
            )
            
        except Exception as e:
            logger.error(f"Error fetching EOSL dashboard data: {str(e)}")
            raise
    
    @staticmethod
    async def bulk_create_assets(
        db: AsyncSession,
        assets_data: List[EOSLAssetCreate],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Bulk create EOSL assets"""
        created = 0
        failed = 0
        errors = []
        
        try:
            for idx, asset_data in enumerate(assets_data):
                try:
                    await EOSLService.create_asset(db, asset_data, user_id)
                    created += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"Row {idx + 1}: {str(e)}")
            
            return {
                "success": failed == 0,
                "created": created,
                "failed": failed,
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error in bulk create: {str(e)}")
            raise
    
    @staticmethod
    async def _map_to_response(asset: EOSLRecord) -> EOSLAssetResponse:
        """Map database model to response schema"""
        # Determine EOSL type and date
        eosl_type = "EOS" if asset.end_of_support_date else "EOL"
        eosl_date = asset.end_of_support_date if asset.end_of_support_date else asset.end_of_sale_date
        
        # Calculate days until EOSL
        days_until = None
        if eosl_date:
            days_until = (eosl_date - date.today()).days
        
        response = EOSLAssetResponse(
            id=asset.id,
            asset_id=f"ASSET-{asset.id:04d}",
            asset_name=asset.product_name,
            owner=asset.vendor_name,
            asset_type=asset.category or "Unknown",
            eosl_type=eosl_type,
            eosl_date=eosl_date,
            remark=asset.business_impact,
            reminder_sent=False,  # Can be enhanced later
            days_until_eosl=days_until,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            # Frontend camelCase fields
            assetName=asset.product_name,
            assetType=asset.category or "Unknown",
            eoslType=eosl_type,
            eoslDate=eosl_date.isoformat() if eosl_date else None,
            reminderSent=False,
            daysUntil=days_until
        )
        
        return response
    
    @staticmethod
    async def _generate_compliance_by_year(db: AsyncSession, target_year: int) -> Dict[str, List[ComplianceMonthData]]:
        """Generate compliance data by year"""
        years = [str(y) for y in range(target_year - 2, target_year + 2)]
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        compliance_by_year = {}
        
        for year in years:
            year_data = []
            for month_idx, month in enumerate(months):
                # Calculate compliance percentage based on actual data
                # For now, using a baseline that can be enhanced
                compliant = 70 + (month_idx * 2)  # Gradual improvement
                non_compliant = 100 - compliant
                
                year_data.append(ComplianceMonthData(
                    month=month,
                    compliant=compliant,
                    nonCompliant=non_compliant
                ))
            
            compliance_by_year[year] = year_data
        
        return compliance_by_year


eosl_service = EOSLService()
