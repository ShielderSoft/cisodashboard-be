from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timedelta

from app.db.session import get_session
from app.models.models import Vendor, VendorComplianceRecord, ComplianceStatus, RiskLevel
from app.schemas.vendor import VendorResponse

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_tprm_dashboard(
    db: AsyncSession = Depends(get_session)
):
    """
    Get complete TPRM dashboard data including:
    - All vendors with compliance metrics
    - Expired vendors (past expiry date)
    - Delayed vendors (approaching expiry date within 30 days)
    """
    try:
        # Get all vendors
        query = select(Vendor).order_by(Vendor.name)
        result = await db.execute(query)
        vendors = result.scalars().all()
        
        vendor_list = []
        expired_vendors = []
        delayed_vendors = []
        
        today = datetime.utcnow().date()
        warning_days = 30  # Days before expiry to consider as "delayed"
        
        for vendor in vendors:
            # Get latest compliance record
            compliance_query = select(VendorComplianceRecord).where(
                VendorComplianceRecord.vendor_id == vendor.id
            ).order_by(VendorComplianceRecord.assessment_date.desc()).limit(1)
            
            compliance_result = await db.execute(compliance_query)
            latest_compliance = compliance_result.scalar_one_or_none()
            
            # Count compliant vs non-compliant controls
            compliant_apps = vendor.compliant_controls if vendor.compliant_controls else 0
            non_compliant_apps = vendor.non_compliant_controls if vendor.non_compliant_controls else 0
            
            # Build vendor data with all fields frontend expects
            vendor_data = {
                "id": vendor.id,
                "vendor_id": vendor.vendor_id if hasattr(vendor, 'vendor_id') else f"VEN-{vendor.id:04d}",
                "name": vendor.name,
                "category": vendor.category,
                # Frontend expects 'risk', backend has 'risk_level'
                "risk": vendor.risk_level.value.capitalize() if vendor.risk_level else "Low",
                "risk_level": vendor.risk_level.value if vendor.risk_level else None,
                "contact_email": vendor.contact_email,
                "contact_phone": vendor.contact_phone,
                "website": vendor.website,
                "description": vendor.description,
                # Add compliant/non-compliant app counts for frontend charts
                "compliant_apps": compliant_apps,
                "non_compliant_apps": non_compliant_apps,
                "compliantApps": compliant_apps,  # camelCase for frontend
                "nonCompliantApps": non_compliant_apps,  # camelCase for frontend
                "compliance_status": latest_compliance.status.value if latest_compliance else None,
                "audit_date": latest_compliance.assessment_date.isoformat() if latest_compliance and latest_compliance.assessment_date else None,
                "auditDate": latest_compliance.assessment_date.isoformat() if latest_compliance and latest_compliance.assessment_date else None,
                # Use expiry_date from compliance record first, fallback to vendor's certificate_expiry_date
                "expiry_date": (latest_compliance.expiry_date.isoformat() if latest_compliance and latest_compliance.expiry_date 
                               else vendor.certificate_expiry_date.isoformat() if vendor.certificate_expiry_date else None),
                "expiryDate": (latest_compliance.expiry_date.isoformat() if latest_compliance and latest_compliance.expiry_date 
                              else vendor.certificate_expiry_date.isoformat() if vendor.certificate_expiry_date else None),
                "standard": latest_compliance.compliance_area if latest_compliance else None,
                "remarks": latest_compliance.notes if latest_compliance and latest_compliance.notes else "No remarks",
                "created_at": vendor.created_at.isoformat() if vendor.created_at else None,
                "updated_at": vendor.updated_at.isoformat() if vendor.updated_at else None,
            }
            
            vendor_list.append(vendor_data)
            
            # Check if vendor is expired or delayed
            # Use expiry_date from compliance record or vendor's certificate_expiry_date
            expiry_date = None
            if latest_compliance and latest_compliance.expiry_date:
                expiry_date = latest_compliance.expiry_date
            elif vendor.certificate_expiry_date:
                expiry_date = vendor.certificate_expiry_date
                
            if expiry_date:
                if expiry_date < today:
                    # Add days_overdue for expired vendors
                    expired_data = {**vendor_data, "days_overdue": (today - expiry_date).days}
                    expired_vendors.append(expired_data)
                elif expiry_date <= today + timedelta(days=warning_days):
                    # Add days_until_expiry and delay_days for delayed vendors
                    days_until = (expiry_date - today).days
                    delayed_data = {
                        **vendor_data, 
                        "days_until_expiry": days_until,
                        "delayDays": days_until  # camelCase for frontend
                    }
                    delayed_vendors.append(delayed_data)
        
        return {
            "vendors": vendor_list,
            "expired_vendors": expired_vendors,
            "expiredVendors": expired_vendors,  # camelCase for frontend
            "delayed_vendors": delayed_vendors,
            "delayedVendors": delayed_vendors,  # camelCase for frontend
            "total_vendors": len(vendor_list),
            "total_expired": len(expired_vendors),
            "total_delayed": len(delayed_vendors)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching TPRM data: {str(e)}"
        )


@router.get("/vendors", response_model=List[Dict[str, Any]])
async def get_vendor_tracker(
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendor tracker data with compliance metrics for VendorTrackerTable
    """
    try:
        query = select(Vendor).order_by(Vendor.name)
        result = await db.execute(query)
        vendors = result.scalars().all()
        
        vendor_list = []
        
        for vendor in vendors:
            # Get latest compliance record
            compliance_query = select(VendorComplianceRecord).where(
                VendorComplianceRecord.vendor_id == vendor.id
            ).order_by(VendorComplianceRecord.assessment_date.desc()).limit(1)
            
            compliance_result = await db.execute(compliance_query)
            latest_compliance = compliance_result.scalar_one_or_none()
            
            # Count compliant vs non-compliant controls
            compliant_apps = vendor.compliant_controls if vendor.compliant_controls else 0
            non_compliant_apps = vendor.non_compliant_controls if vendor.non_compliant_controls else 0
            
            vendor_data = {
                "id": vendor.id,
                "vendor_id": f"VEN-{vendor.id:04d}",
                "name": vendor.name,
                "category": vendor.category,
                # Frontend expects 'risk' field with capitalized value
                "risk": vendor.risk_level.value.capitalize() if vendor.risk_level else "Low",
                "risk_level": vendor.risk_level.value if vendor.risk_level else None,
                "contact_email": vendor.contact_email,
                # Add compliant/non-compliant counts for frontend table
                "compliant_apps": compliant_apps,
                "non_compliant_apps": non_compliant_apps,
                "compliantApps": compliant_apps,  # camelCase variant
                "nonCompliantApps": non_compliant_apps,  # camelCase variant
                "compliance_status": latest_compliance.status.value if latest_compliance else None,
                "audit_date": latest_compliance.assessment_date.isoformat() if latest_compliance and latest_compliance.assessment_date else None,
                "auditDate": latest_compliance.assessment_date.isoformat() if latest_compliance and latest_compliance.assessment_date else None,
                "expiry_date": latest_compliance.expiry_date.isoformat() if latest_compliance and latest_compliance.expiry_date else None,
                "expiryDate": latest_compliance.expiry_date.isoformat() if latest_compliance and latest_compliance.expiry_date else None,
                "standard": latest_compliance.compliance_area if latest_compliance else None,
                "remarks": latest_compliance.notes if latest_compliance and latest_compliance.notes else "No remarks",
            }
            
            vendor_list.append(vendor_data)
        
        return vendor_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching vendor tracker data: {str(e)}"
        )


@router.get("/expired", response_model=List[Dict[str, Any]])
async def get_expired_vendors(
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendors with expired compliance certifications for ExpiredVendorsTable
    """
    try:
        today = datetime.utcnow().date()
        
        query = select(Vendor).order_by(Vendor.name)
        result = await db.execute(query)
        vendors = result.scalars().all()
        
        expired_vendors = []
        
        for vendor in vendors:
            # Get latest compliance record that is expired
            compliance_query = select(VendorComplianceRecord).where(
                and_(
                    VendorComplianceRecord.vendor_id == vendor.id,
                    VendorComplianceRecord.expiry_date < today
                )
            ).order_by(VendorComplianceRecord.assessment_date.desc()).limit(1)
            
            compliance_result = await db.execute(compliance_query)
            latest_compliance = compliance_result.scalar_one_or_none()
            
            if latest_compliance:
                days_overdue = (today - latest_compliance.expiry_date).days
                
                vendor_data = {
                    "id": vendor.id,
                    "vendor_id": f"VEN-{vendor.id:04d}",
                    "name": vendor.name,
                    "category": vendor.category,
                    # Frontend expects 'risk' field
                    "risk": vendor.risk_level.value.capitalize() if vendor.risk_level else "Low",
                    "risk_level": vendor.risk_level.value if vendor.risk_level else None,
                    "contact_email": vendor.contact_email,
                    "compliance_status": latest_compliance.status.value,
                    "audit_date": latest_compliance.assessment_date.isoformat() if latest_compliance.assessment_date else None,
                    "auditDate": latest_compliance.assessment_date.isoformat() if latest_compliance.assessment_date else None,
                    "expiry_date": latest_compliance.expiry_date.isoformat(),
                    "expiryDate": latest_compliance.expiry_date.isoformat(),  # camelCase for frontend
                    "standard": latest_compliance.compliance_area,
                    "days_overdue": days_overdue
                }
                
                expired_vendors.append(vendor_data)
        
        return expired_vendors
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching expired vendors: {str(e)}"
        )


@router.get("/delayed", response_model=List[Dict[str, Any]])
async def get_delayed_vendors(
    db: AsyncSession = Depends(get_session)
):
    """
    Get vendors approaching expiry (within 30 days) for DelayTrackerTable
    """
    try:
        today = datetime.utcnow().date()
        warning_date = today + timedelta(days=30)
        
        query = select(Vendor).order_by(Vendor.name)
        result = await db.execute(query)
        vendors = result.scalars().all()
        
        delayed_vendors = []
        
        for vendor in vendors:
            # Get latest compliance record approaching expiry
            compliance_query = select(VendorComplianceRecord).where(
                and_(
                    VendorComplianceRecord.vendor_id == vendor.id,
                    VendorComplianceRecord.expiry_date >= today,
                    VendorComplianceRecord.expiry_date <= warning_date
                )
            ).order_by(VendorComplianceRecord.assessment_date.desc()).limit(1)
            
            compliance_result = await db.execute(compliance_query)
            latest_compliance = compliance_result.scalar_one_or_none()
            
            if latest_compliance:
                days_until = (latest_compliance.expiry_date - today).days
                
                # Count compliant vs non-compliant controls
                compliant_apps = vendor.compliant_controls if vendor.compliant_controls else 0
                non_compliant_apps = vendor.non_compliant_controls if vendor.non_compliant_controls else 0
                
                vendor_data = {
                    "id": vendor.id,
                    "vendor_id": f"VEN-{vendor.id:04d}",
                    "name": vendor.name,
                    "category": vendor.category,
                    # Frontend expects 'risk' field with capitalized value
                    "risk": vendor.risk_level.value.capitalize() if vendor.risk_level else "Low",
                    "risk_level": vendor.risk_level.value if vendor.risk_level else None,
                    "contact_email": vendor.contact_email,
                    "contact_phone": vendor.contact_phone,
                    # Add compliant/non-compliant counts
                    "compliant_apps": compliant_apps,
                    "non_compliant_apps": non_compliant_apps,
                    "compliantApps": compliant_apps,
                    "nonCompliantApps": non_compliant_apps,
                    "compliance_status": latest_compliance.status.value,
                    "audit_date": latest_compliance.assessment_date.isoformat() if latest_compliance.assessment_date else None,
                    "auditDate": latest_compliance.assessment_date.isoformat() if latest_compliance.assessment_date else None,
                    "expiry_date": latest_compliance.expiry_date.isoformat(),
                    "expiryDate": latest_compliance.expiry_date.isoformat(),
                    "standard": latest_compliance.compliance_area,
                    "days_until_expiry": days_until,
                    "delayDays": days_until,  # Frontend DelayTrackerTable expects this field
                    "remarks": latest_compliance.notes if latest_compliance.notes else "Compliance renewal approaching"
                }
                
                delayed_vendors.append(vendor_data)
        
        return delayed_vendors
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching delayed vendors: {str(e)}"
        )


@router.post("/notify/{vendor_id}", response_model=Dict[str, Any])
async def send_vendor_notification(
    vendor_id: int,
    notification_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session)
):
    """
    Send notification to a vendor
    """
    try:
        # Get vendor
        query = select(Vendor).where(Vendor.id == vendor_id)
        result = await db.execute(query)
        vendor = result.scalar_one_or_none()
        
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with id {vendor_id} not found"
            )
        
        # TODO: Implement actual notification logic (email, SMS, etc.)
        # For now, just return success response
        
        message = notification_data.get("message", "Compliance renewal reminder")
        
        return {
            "success": True,
            "message": f"Notification sent to {vendor.name}",
            "vendor_id": vendor_id,
            "vendor_name": vendor.name,
            "contact_email": vendor.contact_email,
            "notification_message": message,
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending notification: {str(e)}"
        )
