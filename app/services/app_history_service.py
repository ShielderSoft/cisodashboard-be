"""App History service for application vulnerability history tracking"""
import logging
from typing import List
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_
from collections import defaultdict
from calendar import month_name

from app.models.models import Application, Vulnerability, VulnerabilityStatus, RiskLevel
from app.schemas.app_history import (
    AppHistoryResponse, MonthlyTrend, YearlyTrend,
    CategoryData, ApplicationHistoryItem, VulnerabilityCounts
)

logger = logging.getLogger(__name__)


class AppHistoryService:
    """Service for application vulnerability history operations"""
    
    @staticmethod
    async def get_app_history(db: AsyncSession, year: int = None) -> AppHistoryResponse:
        """
        Get complete application vulnerability history data
        
        Args:
            db: Database session
            year: Year to filter data (defaults to current year)
            
        Returns:
            AppHistoryResponse with monthly trends, yearly trends, category data, and applications
        """
        try:
            if year is None:
                year = datetime.now().year
            
            # Month names mapping
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # 1. Build Monthly Trends for the selected year
            monthly_trends = await AppHistoryService._build_monthly_trends(db, year, month_names)
            
            # 2. Build Yearly Trends (current year and 2 previous years)
            yearly_trends = await AppHistoryService._build_yearly_trends(db, year)
            
            # 3. Build Category Data
            category_data = await AppHistoryService._build_category_data(db)
            
            # 4. Build Applications List
            applications = await AppHistoryService._build_applications_list(db)
            
            # 5. Calculate totals from monthly trends
            total_open = sum(month.open for month in monthly_trends)
            total_closed = sum(month.closed for month in monthly_trends)
            
            return AppHistoryResponse(
                monthlyTrends=monthly_trends,
                yearlyTrends=yearly_trends,
                categoryData=category_data,
                applications=applications,
                totalOpen=total_open,
                totalClosed=total_closed
            )
            
        except Exception as e:
            logger.error(f"Error fetching app history data: {str(e)}")
            raise
    
    @staticmethod
    async def _build_monthly_trends(
        db: AsyncSession, 
        year: int,
        month_names: List[str]
    ) -> List[MonthlyTrend]:
        """Build monthly vulnerability trends for the specified year"""
        monthly_data = []
        
        for month_num in range(1, 13):
            month_name = month_names[month_num - 1]
            quarter = ((month_num - 1) // 3) + 1
            
            # Count vulnerabilities opened in this month
            open_stmt = select(func.count(Vulnerability.id)).where(
                and_(
                    extract('year', Vulnerability.discovered_date) == year,
                    extract('month', Vulnerability.discovered_date) == month_num
                )
            )
            open_result = await db.execute(open_stmt)
            open_count = open_result.scalar() or 0
            
            # Count vulnerabilities closed in this month
            closed_stmt = select(func.count(Vulnerability.id)).where(
                and_(
                    Vulnerability.status == VulnerabilityStatus.CLOSED,
                    extract('year', Vulnerability.remediation_completed) == year,
                    extract('month', Vulnerability.remediation_completed) == month_num
                )
            )
            closed_result = await db.execute(closed_stmt)
            closed_count = closed_result.scalar() or 0
            
            monthly_data.append(MonthlyTrend(
                month=month_name,
                quarter=quarter,
                open=open_count,
                closed=closed_count
            ))
        
        return monthly_data
    
    @staticmethod
    async def _build_yearly_trends(db: AsyncSession, current_year: int) -> List[YearlyTrend]:
        """Build yearly vulnerability trends for current year and 2 previous years"""
        yearly_data = []
        
        for year_offset in range(2, -1, -1):  # 2 years ago, 1 year ago, current year
            target_year = current_year - year_offset
            
            # Count closed vulnerabilities by severity for this year
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            for severity in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
                stmt = select(func.count(Vulnerability.id)).where(
                    and_(
                        Vulnerability.status == VulnerabilityStatus.CLOSED,
                        Vulnerability.severity == severity,
                        extract('year', Vulnerability.remediation_completed) == target_year
                    )
                )
                result = await db.execute(stmt)
                count = result.scalar() or 0
                severity_counts[severity.value] = count
            
            yearly_data.append(YearlyTrend(
                year=target_year,
                critical=severity_counts['critical'],
                high=severity_counts['high'],
                medium=severity_counts['medium'],
                low=severity_counts['low']
            ))
        
        return yearly_data
    
    @staticmethod
    async def _build_category_data(db: AsyncSession) -> List[CategoryData]:
        """Build vulnerability data grouped by application category"""
        # Fetch all applications with their vulnerabilities
        app_stmt = select(Application)
        app_result = await db.execute(app_stmt)
        applications = app_result.scalars().all()
        
        # Fetch all open vulnerabilities
        vuln_stmt = select(Vulnerability).where(Vulnerability.status == VulnerabilityStatus.OPEN)
        vuln_result = await db.execute(vuln_stmt)
        vulnerabilities = vuln_result.scalars().all()
        
        # Group vulnerabilities by application
        vuln_by_app = defaultdict(list)
        for vuln in vulnerabilities:
            if vuln.application_id:
                vuln_by_app[vuln.application_id].append(vuln)
        
        # Group by category
        category_vulns = defaultdict(lambda: {'critical': 0, 'high': 0, 'medium': 0, 'low': 0})
        
        # Define categories based on business_criticality or default categories
        for app in applications:
            app_vulns = vuln_by_app.get(app.id, [])
            # Use business_criticality as category, or default to 'General'
            category = app.business_criticality or 'General'
            
            for vuln in app_vulns:
                severity = (vuln.severity or 'low').lower()
                if severity in category_vulns[category]:
                    category_vulns[category][severity] += 1
        
        # If no data, create default categories
        if not category_vulns:
            default_categories = ['IT', 'Finance', 'HR', 'Marketing', 'Operations', 'Customer Service']
            for cat in default_categories:
                category_vulns[cat] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        return [
            CategoryData(
                category=category,
                critical=counts['critical'],
                high=counts['high'],
                medium=counts['medium'],
                low=counts['low']
            )
            for category, counts in sorted(category_vulns.items())
        ]
    
    @staticmethod
    async def _build_applications_list(db: AsyncSession) -> List[ApplicationHistoryItem]:
        """Build list of applications with vulnerability counts"""
        # Fetch all applications
        app_stmt = select(Application)
        app_result = await db.execute(app_stmt)
        applications = app_result.scalars().all()
        
        # Fetch all open vulnerabilities
        vuln_stmt = select(Vulnerability).where(Vulnerability.status == VulnerabilityStatus.OPEN)
        vuln_result = await db.execute(vuln_stmt)
        vulnerabilities = vuln_result.scalars().all()
        
        # Group vulnerabilities by application
        vuln_by_app = defaultdict(list)
        for vuln in vulnerabilities:
            if vuln.application_id:
                vuln_by_app[vuln.application_id].append(vuln)
        
        # Build application list
        app_list = []
        for app in applications:
            app_vulns = vuln_by_app.get(app.id, [])
            
            # Count by severity
            counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            for vuln in app_vulns:
                severity = (vuln.severity or 'low').lower()
                if severity in counts:
                    counts[severity] += 1
            
            app_list.append(ApplicationHistoryItem(
                id=f"APP-{app.id}",
                name=app.name,
                category=app.business_criticality or 'General',
                vulnerabilities=VulnerabilityCounts(
                    critical=counts['critical'],
                    high=counts['high'],
                    medium=counts['medium'],
                    low=counts['low']
                )
            ))
        
        return app_list


# Create singleton instance
app_history_service = AppHistoryService()
