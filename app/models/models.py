from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey, JSON, Numeric, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import enum

from app.db.session import Base


class UserRole(str, Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    CISO = "ciso"
    SECURITY_ANALYST = "security_analyst"
    COMPLIANCE_OFFICER = "compliance_officer"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class RiskLevel(str, Enum):
    """Risk levels enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceStatus(str, Enum):
    """Compliance status enumeration"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    EXCEPTION = "exception"
    NOT_APPLICABLE = "not_applicable"


class VulnerabilityStatus(str, Enum):
    """Vulnerability status enumeration"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED_RISK = "accepted_risk"


class ApplicationType(str, Enum):
    """Application type enumeration"""
    WEB_APPLICATION = "web_application"
    MOBILE_APPLICATION = "mobile_application"
    DESKTOP_APPLICATION = "desktop_application"
    API_SERVICE = "api_service"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    THIRD_PARTY = "third_party"


class ExceptionCategory(str, Enum):
    """Exception category enumeration"""
    COMPLIANCE = "compliance"
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    OTHER = "other"


class ExceptionSeverity(str, Enum):
    """Exception severity enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExceptionStatus(str, Enum):
    """Exception status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"


class TimestampMixin:
    """Mixin to add timestamp fields to models"""
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Relationships
    created_applications = relationship("Application", back_populates="owner_user")
    assigned_vulnerabilities = relationship("Vulnerability", back_populates="assigned_to")
    audit_logs = relationship("AuditLog", back_populates="user")


class Organization(Base, TimestampMixin):
    """Organization model"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Relationships
    applications = relationship("Application", back_populates="organization")
    vendors = relationship("Vendor", back_populates="organization")
    exceptions = relationship("Exception", back_populates="organization")


class Application(Base, TimestampMixin):
    """Application model"""
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    application_type = Column(SQLEnum(ApplicationType), nullable=False)
    version = Column(String(50), nullable=True)
    url = Column(String(500), nullable=True)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False)
    business_criticality = Column(String(50), nullable=True)
    data_classification = Column(String(50), nullable=True)
    
    # Owner and vendor information (string fields for simple data entry)
    owner = Column(String(255), nullable=True)  # Owner name/email
    vendor_name = Column(String(255), nullable=True)  # Vendor name if third-party
    
    # Foreign keys (for future relationships)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Technical details
    technology_stack = Column(JSON, nullable=True)  # Store as JSON
    environment = Column(String(50), nullable=True)  # dev, staging, production
    hosting_type = Column(String(50), nullable=True)  # cloud, on-premise, hybrid
    
    # Compliance and security
    compliance_requirements = Column(JSON, nullable=True)  # List of compliance standards
    last_security_review = Column(Date, nullable=True)
    next_security_review = Column(Date, nullable=True)
    
    # Relationships
    owner_user = relationship("User", back_populates="created_applications", foreign_keys=[owner_id])
    organization = relationship("Organization", back_populates="applications")
    vulnerabilities = relationship("Vulnerability", back_populates="application")
    compliance_records = relationship("ComplianceRecord", back_populates="application")
    certificates = relationship("VendorCertificate", back_populates="application")


class Vendor(Base, TimestampMixin):
    """Vendor model for TPRM (Third Party Risk Management)"""
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # Software, Hardware, Service, etc.
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Risk assessment
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False)
    last_risk_assessment = Column(Date, nullable=True)
    next_risk_assessment = Column(Date, nullable=True)
    
    # Contract information
    contract_start_date = Column(Date, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    contract_value = Column(Numeric(15, 2), nullable=True)
    
    # Compliance status
    compliance_status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.PENDING, nullable=False)
    
    # Compliance metrics - calculated from assessments
    compliance_rate = Column(Numeric(5, 2), nullable=True)  # Percentage (0-100)
    compliant_controls = Column(Integer, default=0, nullable=False)
    non_compliant_controls = Column(Integer, default=0, nullable=False)
    last_compliance_check = Column(Date, nullable=True)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="vendors")
    compliance_records = relationship("VendorComplianceRecord", back_populates="vendor")
    vulnerabilities = relationship("Vulnerability", back_populates="vendor")
    certificates = relationship("VendorCertificate", back_populates="vendor")


class Vulnerability(Base, TimestampMixin):
    """Vulnerability model"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cve_id = Column(String(20), nullable=True, index=True)  # CVE-2023-1234
    severity = Column(SQLEnum(RiskLevel), nullable=False)
    status = Column(SQLEnum(VulnerabilityStatus), default=VulnerabilityStatus.OPEN, nullable=False, index=True)
    
    # Discovery information
    discovered_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    source = Column(String(100), nullable=True)  # Scanner, Manual, External report, etc.
    
    # Risk scoring
    cvss_score = Column(Numeric(3, 1), nullable=True)  # 0.0 to 10.0
    cvss_vector = Column(String(200), nullable=True)
    exploit_available = Column(Boolean, default=False, nullable=False)
    
    # Remediation
    remediation_plan = Column(Text, nullable=True)
    remediation_deadline = Column(Date, nullable=True)
    remediation_completed = Column(DateTime(timezone=True), nullable=True)
    
    # Closure tracking fields
    remarks = Column(Text, nullable=True)
    poc_file_path = Column(String(500), nullable=True)
    
    # Foreign keys
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    application = relationship("Application", back_populates="vulnerabilities")
    vendor = relationship("Vendor", back_populates="vulnerabilities")
    assigned_to = relationship("User", back_populates="assigned_vulnerabilities")


class ComplianceStandard(Base, TimestampMixin):
    """Compliance standards model"""
    __tablename__ = "compliance_standards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # ISO27001, PCI_DSS, etc.
    full_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=True)
    authority = Column(String(255), nullable=True)  # ISO, PCI Council, etc.
    
    # Relationships
    requirements = relationship("ComplianceRequirement", back_populates="standard")
    compliance_records = relationship("ComplianceRecord", back_populates="standard")


class ComplianceRequirement(Base, TimestampMixin):
    """Individual compliance requirements"""
    __tablename__ = "compliance_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(String(50), nullable=False, index=True)  # e.g., "A.5.1.1"
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    
    # Foreign keys
    standard_id = Column(Integer, ForeignKey("compliance_standards.id"), nullable=False)
    
    # Relationships
    standard = relationship("ComplianceStandard", back_populates="requirements")


class ComplianceRecord(Base, TimestampMixin):
    """Compliance records for applications"""
    __tablename__ = "compliance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(ComplianceStatus), nullable=False)
    assessment_date = Column(Date, nullable=False)
    next_assessment_date = Column(Date, nullable=True)
    evidence = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    standard_id = Column(Integer, ForeignKey("compliance_standards.id"), nullable=False)
    assessor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    application = relationship("Application", back_populates="compliance_records")
    standard = relationship("ComplianceStandard", back_populates="compliance_records")
    assessor = relationship("User")


class VendorComplianceRecord(Base, TimestampMixin):
    """Compliance records for vendors"""
    __tablename__ = "vendor_compliance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    compliance_area = Column(String(255), nullable=False)  # Security, Privacy, etc.
    status = Column(SQLEnum(ComplianceStatus), nullable=False)
    assessment_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    certificate_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    assessor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="compliance_records")
    assessor = relationship("User")


class VendorCertificate(Base, TimestampMixin):
    """Vendor certificates for compliance standards"""
    __tablename__ = "vendor_certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_type = Column(String(100), nullable=False)  # ISO 27001, PCI-DSS, etc.
    certificate_number = Column(String(255), nullable=True)
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.COMPLIANT, nullable=False)
    
    # Certificate details
    issuing_authority = Column(String(255), nullable=True)
    certificate_url = Column(String(500), nullable=True)
    scope = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="certificates")
    application = relationship("Application", back_populates="certificates")


class EOSLRecord(Base, TimestampMixin):
    """End of Service Life tracking"""
    __tablename__ = "eosl_records"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)  # OS, Database, Framework, etc.
    
    # EOSL dates
    end_of_sale_date = Column(Date, nullable=True)
    end_of_support_date = Column(Date, nullable=True)
    end_of_extended_support_date = Column(Date, nullable=True)
    
    # Risk and impact
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    business_impact = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)
    remediation_deadline = Column(Date, nullable=True)
    
    # Foreign keys
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    application = relationship("Application")
    owner = relationship("User")


class AuditLog(Base, TimestampMixin):
    """Audit log for tracking all system activities"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)  # User, Application, Vulnerability, etc.
    resource_id = Column(String(100), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class Notification(Base, TimestampMixin):
    """Notifications system"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # info, warning, error, success
    is_read = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User")


class Exception(Base, TimestampMixin):
    """Exception tracking model for compliance and operational exceptions"""
    __tablename__ = "exceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    exception_name = Column(String(255), nullable=False, index=True)
    category = Column(SQLEnum(ExceptionCategory), nullable=False)
    severity = Column(SQLEnum(ExceptionSeverity), nullable=False)
    status = Column(SQLEnum(ExceptionStatus), nullable=False, default=ExceptionStatus.PENDING)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    comments = Column(Text, nullable=True)
    
    # Additional tracking fields
    risk_assessment = Column(Text, nullable=True)
    mitigation_plan = Column(Text, nullable=True)
    approval_status = Column(String(50), nullable=True, default="pending")  # pending, approved, rejected
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="exceptions")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class Assignment(Base, TimestampMixin):
    """Assignment grouping for assessments (e.g., quarterly assessment)"""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)  # open, in_progress, completed

    # Foreign keys
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    standard_id = Column(Integer, ForeignKey("compliance_standards.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)

    # Relationships
    vendor = relationship("Vendor")
    standard = relationship("ComplianceStandard")
    created_by = relationship("User")
    assessments = relationship("Assessment", back_populates="assignment")


class Assessment(Base, TimestampMixin):
    """Assessment record per control under an assignment"""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    # Link to a compliance requirement if available
    compliance_requirement_id = Column(Integer, ForeignKey("compliance_requirements.id"), nullable=True)
    control_identifier = Column(String(100), nullable=True)  # e.g., 'C1.1' or 'A5.1.1'
    compliant = Column(Boolean, default=False, nullable=False)
    remark = Column(Text, nullable=True)
    poc = Column(String(500), nullable=True)
    status = Column(String(50), nullable=True)  # implemented, notImplemented, notApplicable
    assessor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="assessments")
    vendor = relationship("Vendor")
    compliance_requirement = relationship("ComplianceRequirement")
    assessor = relationship("User")


class ApplicationReminder(Base, TimestampMixin):
    """Application reminder tracking model"""
    __tablename__ = "application_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Owner who was reminded
    reminder_sent_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    reminder_type = Column(String(50), default="vulnerability_delay")  # Type of reminder
    notes = Column(Text, nullable=True)
    
    # Relationships
    application = relationship("Application")
    owner = relationship("User")