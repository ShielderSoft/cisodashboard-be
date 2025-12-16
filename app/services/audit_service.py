"""
Audit service for aggregating compliance statistics and dashboard data
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Dict, List
from datetime import datetime, timedelta

from app.models.models import Vendor, Application, VendorCertificate
from app.schemas.audit import (
    AuditStatisticsResponse,
    ComplianceDataResponse,
    TopVendorItem,
    TopVendorsResponse
)


class AuditService:
    """Service for audit dashboard statistics and compliance data"""

    @staticmethod
    async def get_statistics(db: AsyncSession) -> AuditStatisticsResponse:
        """
        Get overall audit statistics: compliant, non-compliant, and exception counts
        
        Compliance logic:
        - A vendor is compliant if it has at least one valid ISO 27001 AND one valid PCI-DSS certificate
        - Non-compliant: vendors that don't meet the compliance criteria
        - Exceptions: vendors with expired certificates or missing required certificates
        """
        # Get all vendors with their certificates (eagerly loaded)
        stmt = select(Vendor).options(selectinload(Vendor.certificates))
        result = await db.execute(stmt)
        vendors = result.scalars().unique().all()

        compliant_count = 0
        non_compliant_count = 0
        exceptions_count = 0

        for vendor in vendors:
            # Check if vendor has valid ISO 27001 certificate
            has_valid_iso = any(
                cert.certificate_type == "ISO 27001" 
                and cert.status == "active"
                and cert.expiry_date >= datetime.now().date()
                for cert in vendor.certificates
            )

            # Check if vendor has valid PCI-DSS certificate
            has_valid_pci = any(
                cert.certificate_type in ["PCI-DSS", "PCI-DSS v4", "PCI DSS"]
                and cert.status == "active"
                and cert.expiry_date >= datetime.now().date()
                for cert in vendor.certificates
            )

            # Check for expired certificates
            has_expired_cert = any(
                cert.expiry_date < datetime.now().date()
                for cert in vendor.certificates
            )

            # Determine vendor status
            if has_valid_iso and has_valid_pci:
                compliant_count += 1
            elif has_expired_cert or (not has_valid_iso and not has_valid_pci):
                if has_expired_cert:
                    exceptions_count += 1
                else:
                    non_compliant_count += 1
            else:
                non_compliant_count += 1

        # For trends, we'll use simple percentages (can be enhanced with historical data)
        total = len(vendors)
        compliant_trend = (compliant_count / total * 100) if total > 0 else 0
        non_compliant_trend = (non_compliant_count / total * 100) if total > 0 else 0
        exceptions_trend = (exceptions_count / total * 100) if total > 0 else 0

        return AuditStatisticsResponse(
            compliant=compliant_count,
            non_compliant=non_compliant_count,
            exceptions=exceptions_count,
            compliant_trend=round(compliant_trend, 1),
            non_compliant_trend=round(non_compliant_trend, 1),
            exceptions_trend=round(exceptions_trend, 1)
        )

    @staticmethod
    async def get_iso27001_compliance(db: AsyncSession) -> ComplianceDataResponse:
        """
        Get ISO 27001 compliance data for applications
        
        An application is ISO compliant if it has at least one valid ISO 27001 certificate
        """
        # Get all applications with their certificates (eagerly loaded)
        stmt = select(Application).options(selectinload(Application.certificates))
        result = await db.execute(stmt)
        applications = result.scalars().unique().all()

        compliant_count = 0
        non_compliant_count = 0

        for app in applications:
            # Check if application has valid ISO 27001 certificate
            has_valid_iso = any(
                cert.certificate_type == "ISO 27001"
                and cert.status == "active"
                and cert.expiry_date >= datetime.now().date()
                for cert in app.certificates
            )

            if has_valid_iso:
                compliant_count += 1
            else:
                non_compliant_count += 1

        total = len(applications)
        compliant_percentage = (compliant_count / total * 100) if total > 0 else 0

        return ComplianceDataResponse(
            compliant=compliant_count,
            non_compliant=non_compliant_count,
            total=total,
            compliant_percentage=round(compliant_percentage, 1)
        )

    @staticmethod
    async def get_pcidss_compliance(db: AsyncSession) -> ComplianceDataResponse:
        """
        Get PCI-DSS compliance data for applications
        
        An application is PCI-DSS compliant if it has at least one valid PCI-DSS certificate
        """
        # Get all applications with their certificates (eagerly loaded)
        stmt = select(Application).options(selectinload(Application.certificates))
        result = await db.execute(stmt)
        applications = result.scalars().unique().all()

        compliant_count = 0
        non_compliant_count = 0

        for app in applications:
            # Check if application has valid PCI-DSS certificate
            has_valid_pci = any(
                cert.certificate_type in ["PCI-DSS", "PCI-DSS v4", "PCI DSS"]
                and cert.status == "active"
                and cert.expiry_date >= datetime.now().date()
                for cert in app.certificates
            )

            if has_valid_pci:
                compliant_count += 1
            else:
                non_compliant_count += 1

        total = len(applications)
        compliant_percentage = (compliant_count / total * 100) if total > 0 else 0

        return ComplianceDataResponse(
            compliant=compliant_count,
            non_compliant=non_compliant_count,
            total=total,
            compliant_percentage=round(compliant_percentage, 1)
        )

    @staticmethod
    async def get_top_vendors(db: AsyncSession, limit: int = 5) -> TopVendorsResponse:
        """
        Get top vendors by certificate count with compliance breakdown
        
        Returns top N vendors sorted by number of certificates,
        with breakdown of compliant vs non-compliant certificates
        """
        # Get all vendors with their certificates (eagerly loaded)
        stmt = select(Vendor).options(selectinload(Vendor.certificates))
        result = await db.execute(stmt)
        vendors = result.scalars().unique().all()

        # Calculate certificate counts and compliance for each vendor
        vendor_data = []
        for vendor in vendors:
            if not vendor.certificates:
                continue

            total_certs = len(vendor.certificates)
            compliant_certs = 0

            for cert in vendor.certificates:
                # Check if certificate is valid (not expired and active)
                is_valid = (
                    cert.status == "active"
                    and cert.expiry_date >= datetime.now().date()
                )
                
                if is_valid:
                    compliant_certs += 1

            non_compliant_certs = total_certs - compliant_certs
            compliant_percentage = (compliant_certs / total_certs * 100) if total_certs > 0 else 0

            vendor_data.append({
                'name': vendor.name,
                'total': total_certs,
                'compliant': compliant_certs,
                'non_compliant': non_compliant_certs,
                'compliant_percentage': str(int(compliant_percentage))
            })

        # Sort by total certificates (descending) and take top N
        vendor_data.sort(key=lambda x: x['total'], reverse=True)
        top_vendors = vendor_data[:limit]

        # Convert to TopVendorItem objects
        vendor_items = [
            TopVendorItem(
                name=v['name'],
                compliant=v['compliant'],
                non_compliant=v['non_compliant'],
                total=v['total'],
                compliant_percentage=v['compliant_percentage']
            )
            for v in top_vendors
        ]

        return TopVendorsResponse(vendors=vendor_items)


# Create a singleton instance
audit_service = AuditService()
