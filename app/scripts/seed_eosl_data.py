"""
Seed script for EOSL data
Creates sample EOSL records for testing
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal
from app.models.models import EOSLRecord, RiskLevel
from sqlalchemy import select


async def seed_eosl_data():
    """Seed sample EOSL data"""
    async with SessionLocal() as db:
        try:
            # Check if data already exists
            result = await db.execute(select(EOSLRecord))
            existing = result.scalars().first()
            
            if existing:
                print("✅ EOSL data already exists. Skipping seed.")
                return
            
            # Asset types
            asset_types = [
                'Server', 'Network Switch', 'Database', 'Firewall',
                'Router', 'Storage Array', 'Load Balancer', 'Workstation',
                'Virtual Machine', 'Container Host', 'VPN Gateway', 'Backup System'
            ]
            
            # Vendors/Owners
            vendors = [
                'John Smith', 'Emily Johnson', 'Michael Wilson',
                'Sarah Brown', 'David Miller', 'Jennifer Davis',
                'Robert Taylor', 'Jessica Anderson', 'Thomas Martinez'
            ]
            
            # Sample asset names
            asset_names = [
                'Production Server 01', 'Database Cluster 03', 'Firewall Edge 05',
                'Core Router 02', 'Storage SAN 01', 'Load Balancer Primary',
                'Backup Server 02', 'VM Host 04', 'Network Switch Floor 3',
                'VPN Gateway Remote', 'Application Server 06', 'Web Server 08',
                'Email Server 01', 'File Server 02', 'DNS Server 01',
                'Proxy Server 01', 'Monitoring Server', 'Log Server',
                'Dev Server 01', 'Test Server 02'
            ]
            
            print("🌱 Seeding EOSL data...")
            
            today = datetime.now().date()
            created_count = 0
            
            # Create 20 sample EOSL records
            for i in range(20):
                # Randomly decide if EOS or EOL
                is_eos = random.choice([True, False])
                
                # Generate date (some expired, some expiring soon, some future)
                days_offset = random.randint(-30, 365)
                eosl_date = today + timedelta(days=days_offset)
                
                # Create record
                record = EOSLRecord(
                    product_name=random.choice(asset_names),
                    vendor_name=random.choice(vendors),
                    category=random.choice(asset_types),
                    version=f"v{random.randint(1, 10)}.{random.randint(0, 9)}",
                    end_of_support_date=eosl_date if is_eos else None,
                    end_of_sale_date=eosl_date if not is_eos else None,
                    end_of_extended_support_date=eosl_date + timedelta(days=180) if is_eos else None,
                    risk_level=RiskLevel.MEDIUM if is_eos else RiskLevel.HIGH,
                    business_impact=f"Sample remark for asset {i+1}",
                    remediation_plan=f"Upgrade to newer version before {eosl_date.isoformat()}"
                )
                
                db.add(record)
                created_count += 1
            
            await db.commit()
            print(f"✅ Successfully created {created_count} EOSL records")
            
        except Exception as e:
            print(f"❌ Error seeding EOSL data: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("🚀 Starting EOSL data seeding...")
    asyncio.run(seed_eosl_data())
    print("✨ EOSL seeding complete!")
