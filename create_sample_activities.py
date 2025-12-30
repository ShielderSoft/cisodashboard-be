#!/usr/bin/env python3
"""
Script to create sample activity log entries for testing the General Updates component
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.services.activity_service import ActivityLogService
from app.schemas.activity_log import ActivityLogCreate, ActivityTypeEnum, ActivityPriorityEnum


async def create_sample_activities():
    """Create sample activity log entries"""
    
    async with SessionLocal() as db:
        print("Creating sample activity logs...")
        
        # Sample activities for the last 7 days
        activities = [
            ActivityLogCreate(
                activity_type="application_created",
                priority="medium",
                title="New Application Added",
                description="Customer Portal application was successfully added to the system",
                user_id=1,
                user_name="John Doe",
                entity_type="application",
                entity_id=101,
                entity_name="Customer Portal",
                extra_data={"environment": "production", "type": "web"},
                tags=["application", "web", "production"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.VULNERABILITY_CREATED,
                priority=ActivityPriorityEnum.HIGH,
                title="Critical Vulnerability Detected",
                description="CVE-2024-1234: Remote Code Execution vulnerability found in payment gateway",
                user_id=2,
                user_name="Security Scanner",
                entity_type="vulnerability",
                entity_id=501,
                entity_name="CVE-2024-1234",
                extra_data={"severity": "CRITICAL", "cvss_score": 9.8},
                tags=["vulnerability", "critical", "rce"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.VENDOR_UPDATED,
                priority=ActivityPriorityEnum.MEDIUM,
                title="Vendor Information Updated",
                description="AWS Cloud Services vendor profile was updated with new contact information",
                user_id=1,
                user_name="John Doe",
                entity_type="vendor",
                entity_id=25,
                entity_name="AWS Cloud Services",
                extra_data={"changes": ["contact_email", "compliance_status"]},
                tags=["vendor", "cloud", "update"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.CERTIFICATE_EXPIRING_SOON,
                priority=ActivityPriorityEnum.HIGH,
                title="SSL Certificate Expiring Soon",
                description="SSL certificate for *.example.com will expire in 15 days",
                user_id=None,
                user_name="System",
                entity_type="certificate",
                entity_id=78,
                entity_name="*.example.com",
                extra_data={"expires_at": "2025-01-15", "days_remaining": 15},
                tags=["certificate", "ssl", "expiring"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.COMPLIANCE_STATUS_CHANGED,
                priority=ActivityPriorityEnum.HIGH,
                title="Compliance Status Changed",
                description="SOC 2 compliance status changed from 'In Progress' to 'Compliant'",
                user_id=3,
                user_name="Compliance Team",
                entity_type="compliance",
                entity_id=12,
                entity_name="SOC 2 Audit",
                extra_data={"old_status": "in_progress", "new_status": "compliant"},
                tags=["compliance", "soc2", "audit"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.EXCEPTION_CREATED,
                priority=ActivityPriorityEnum.MEDIUM,
                title="Security Exception Requested",
                description="Exception request for outdated Java version on legacy payment system",
                user_id=4,
                user_name="Dev Team Lead",
                entity_type="exception",
                entity_id=89,
                entity_name="Legacy Payment System - Java 8",
                extra_data={"reason": "critical_business_app", "duration": "90_days"},
                tags=["exception", "legacy", "java"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.EOSL_ASSET_EXPIRING_SOON,
                priority=ActivityPriorityEnum.CRITICAL,
                title="EOSL Asset End of Life Warning",
                description="Windows Server 2012 R2 will reach end of support in 30 days",
                user_id=None,
                user_name="System",
                entity_type="eosl",
                entity_id=45,
                entity_name="Windows Server 2012 R2",
                extra_data={"eol_date": "2025-01-30", "affected_servers": 12},
                tags=["eosl", "windows", "critical"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.USER_LOGIN,
                priority=ActivityPriorityEnum.LOW,
                title="Administrator Login",
                description="Admin user logged in from new location",
                user_id=1,
                user_name="John Doe",
                entity_type="user",
                entity_id=1,
                entity_name="john.doe@example.com",
                extra_data={"ip": "192.168.1.100", "location": "New York, US"},
                tags=["user", "login", "admin"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.AUDIT_COMPLETED,
                priority=ActivityPriorityEnum.HIGH,
                title="Security Audit Completed",
                description="Q4 2024 security audit completed with 3 high-priority findings",
                user_id=3,
                user_name="Compliance Team",
                entity_type="audit",
                entity_id=67,
                entity_name="Q4 2024 Security Audit",
                extra_data={"findings": {"critical": 0, "high": 3, "medium": 12, "low": 25}},
                tags=["audit", "security", "quarterly"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.VULNERABILITY_CLOSED,
                priority=ActivityPriorityEnum.MEDIUM,
                title="Vulnerability Remediated",
                description="SQL Injection vulnerability in admin panel has been fixed and verified",
                user_id=2,
                user_name="Security Team",
                entity_type="vulnerability",
                entity_id=502,
                entity_name="SQL Injection - Admin Panel",
                extra_data={"remediation_time_days": 5, "verified": True},
                tags=["vulnerability", "closed", "sql-injection"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.APPLICATION_UPDATED,
                priority=ActivityPriorityEnum.LOW,
                title="Application Configuration Updated",
                description="Payment Gateway application security settings were updated",
                user_id=1,
                user_name="John Doe",
                entity_type="application",
                entity_id=102,
                entity_name="Payment Gateway",
                extra_data={"changes": ["firewall_rules", "encryption_settings"]},
                tags=["application", "security", "configuration"]
            ),
            ActivityLogCreate(
                activity_type=ActivityTypeEnum.SYSTEM_ALERT,
                priority=ActivityPriorityEnum.CRITICAL,
                title="System Alert: High Memory Usage",
                description="Database server experiencing high memory usage (95%)",
                user_id=None,
                user_name="Monitoring System",
                entity_type="system",
                entity_id=None,
                entity_name="DB-PROD-01",
                extra_data={"memory_usage": 95, "threshold": 85},
                tags=["system", "alert", "database", "performance"]
            ),
        ]
        
        # Create activities with different timestamps
        created_count = 0
        for i, activity in enumerate(activities):
            try:
                # Offset timestamps to spread across last 7 days
                days_ago = i % 7
                created_activity = await ActivityLogService.create_activity(db, activity)
                created_count += 1
                print(f"✅ Created: {activity.title}")
            except Exception as e:
                print(f"❌ Failed to create '{activity.title}': {e}")
        
        print(f"\n✅ Successfully created {created_count} out of {len(activities)} sample activities!")


if __name__ == "__main__":
    asyncio.run(create_sample_activities())
