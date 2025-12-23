"""
Seed script to add test TPRM data with expired and delayed compliance records
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.models import Vendor, VendorComplianceRecord, ComplianceStatus, RiskLevel


async def seed_tprm_data():
    """Seed test data for TPRM with expired and delayed vendors"""
    async with SessionLocal() as db:
        try:
            today = datetime.utcnow().date()
            
            # Get existing vendors
            result = await db.execute(select(Vendor).limit(5))
            vendors = result.scalars().all()
            
            if not vendors:
                print("No vendors found in database. Please add vendors first.")
                return
            
            print(f"Found {len(vendors)} vendors. Adding compliance records...")
            
            # Add expired compliance records (expiry_date in the past)
            if len(vendors) >= 1:
                vendor = vendors[0]
                expired_date = today - timedelta(days=30)  # Expired 30 days ago
                assessment_date = expired_date - timedelta(days=365)  # Assessed 1 year before expiry
                
                # Check if record already exists
                existing = await db.execute(
                    select(VendorComplianceRecord).where(
                        VendorComplianceRecord.vendor_id == vendor.id,
                        VendorComplianceRecord.expiry_date == expired_date
                    )
                )
                if not existing.scalar_one_or_none():
                    expired_record = VendorComplianceRecord(
                        vendor_id=vendor.id,
                        compliance_area="ISO27001 Certification",
                        status=ComplianceStatus.NON_COMPLIANT,
                        assessment_date=assessment_date,
                        expiry_date=expired_date,
                        notes="Certificate has expired and needs renewal"
                    )
                    db.add(expired_record)
                    print(f"✅ Added EXPIRED compliance record for vendor: {vendor.name} (expired {(today - expired_date).days} days ago)")
            
            if len(vendors) >= 2:
                vendor = vendors[1]
                expired_date = today - timedelta(days=15)  # Expired 15 days ago
                assessment_date = expired_date - timedelta(days=180)
                
                existing = await db.execute(
                    select(VendorComplianceRecord).where(
                        VendorComplianceRecord.vendor_id == vendor.id,
                        VendorComplianceRecord.expiry_date == expired_date
                    )
                )
                if not existing.scalar_one_or_none():
                    expired_record = VendorComplianceRecord(
                        vendor_id=vendor.id,
                        compliance_area="SOC2 Type II",
                        status=ComplianceStatus.NON_COMPLIANT,
                        assessment_date=assessment_date,
                        expiry_date=expired_date,
                        notes="SOC2 certification expired, renewal in progress"
                    )
                    db.add(expired_record)
                    print(f"✅ Added EXPIRED compliance record for vendor: {vendor.name} (expired {(today - expired_date).days} days ago)")
            
            # Add delayed compliance records (expiry_date approaching - within 30 days)
            if len(vendors) >= 3:
                vendor = vendors[2]
                delayed_date = today + timedelta(days=15)  # Expires in 15 days
                assessment_date = delayed_date - timedelta(days=350)
                
                existing = await db.execute(
                    select(VendorComplianceRecord).where(
                        VendorComplianceRecord.vendor_id == vendor.id,
                        VendorComplianceRecord.expiry_date == delayed_date
                    )
                )
                if not existing.scalar_one_or_none():
                    delayed_record = VendorComplianceRecord(
                        vendor_id=vendor.id,
                        compliance_area="GDPR Compliance",
                        status=ComplianceStatus.PENDING,
                        assessment_date=assessment_date,
                        expiry_date=delayed_date,
                        notes="GDPR certification expiring soon, renewal scheduled"
                    )
                    db.add(delayed_record)
                    print(f"✅ Added DELAYED compliance record for vendor: {vendor.name} (expires in {(delayed_date - today).days} days)")
            
            if len(vendors) >= 4:
                vendor = vendors[3]
                delayed_date = today + timedelta(days=25)  # Expires in 25 days
                assessment_date = delayed_date - timedelta(days=365)
                
                existing = await db.execute(
                    select(VendorComplianceRecord).where(
                        VendorComplianceRecord.vendor_id == vendor.id,
                        VendorComplianceRecord.expiry_date == delayed_date
                    )
                )
                if not existing.scalar_one_or_none():
                    delayed_record = VendorComplianceRecord(
                        vendor_id=vendor.id,
                        compliance_area="PCI DSS",
                        status=ComplianceStatus.PENDING,
                        assessment_date=assessment_date,
                        expiry_date=delayed_date,
                        notes="PCI DSS audit approaching, documentation being prepared"
                    )
                    db.add(delayed_record)
                    print(f"✅ Added DELAYED compliance record for vendor: {vendor.name} (expires in {(delayed_date - today).days} days)")
            
            if len(vendors) >= 5:
                vendor = vendors[4]
                delayed_date = today + timedelta(days=7)  # Expires in 7 days - URGENT!
                assessment_date = delayed_date - timedelta(days=180)
                
                existing = await db.execute(
                    select(VendorComplianceRecord).where(
                        VendorComplianceRecord.vendor_id == vendor.id,
                        VendorComplianceRecord.expiry_date == delayed_date
                    )
                )
                if not existing.scalar_one_or_none():
                    delayed_record = VendorComplianceRecord(
                        vendor_id=vendor.id,
                        compliance_area="HIPAA Certification",
                        status=ComplianceStatus.PENDING,
                        assessment_date=assessment_date,
                        expiry_date=delayed_date,
                        notes="URGENT: HIPAA certification expiring in 1 week!"
                    )
                    db.add(delayed_record)
                    print(f"⚠️  Added URGENT DELAYED compliance record for vendor: {vendor.name} (expires in {(delayed_date - today).days} days)")
            
            await db.commit()
            print("\n✅ Successfully seeded TPRM test data!")
            print(f"   - 2 expired vendor compliance records")
            print(f"   - 3 delayed/approaching expiry compliance records")
            print("\nYou can now test the TPRM endpoints:")
            print("   GET /api/v1/tprm/")
            print("   GET /api/v1/tprm/expired")
            print("   GET /api/v1/tprm/delayed")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding data: {str(e)}")
            raise


if __name__ == "__main__":
    print("🌱 Seeding TPRM test data...")
    asyncio.run(seed_tprm_data())
