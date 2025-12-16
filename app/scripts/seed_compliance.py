"""
Seed script to populate compliance-related sample data similar to frontend mockData.
Run this script with the project's Python environment and ensure DB is reachable.
"""
from datetime import date, timedelta
from decimal import Decimal
from app.db.session import SyncSessionLocal
from app.models.models import (
    ComplianceStandard, ComplianceRequirement, Vendor, Assignment, Assessment
)

# Simple helper to create or get

def upsert(session, model, lookup, **kwargs):
    obj = session.query(model).filter_by(**lookup).first()
    if obj:
        for k, v in kwargs.items():
            setattr(obj, k, v)
    else:
        obj = model(**{**lookup, **kwargs})
        session.add(obj)
    return obj


def seed():
    session = SyncSessionLocal()
    try:
        # Create standards
        iso = upsert(session, ComplianceStandard, {'name': 'ISO_27001'}, 
                    full_name='ISO 27001:2013 - Information Security Management System', 
                    version='2013',
                    description='International standard for information security management')
        
        pci = upsert(session, ComplianceStandard, {'name': 'PCIDSS_V4'}, 
                    full_name='PCI DSS v4.0 - Payment Card Industry Data Security Standard', 
                    version='4.0',
                    description='Security standard for organizations that handle credit cards')
        
        soc2 = upsert(session, ComplianceStandard, {'name': 'SOC2'}, 
                     full_name='SOC 2 Type II - Service Organization Control 2', 
                     version='Type II',
                     description='Audit standard for service providers storing customer data')
        
        gdpr = upsert(session, ComplianceStandard, {'name': 'GDPR'}, 
                     full_name='GDPR - General Data Protection Regulation', 
                     version='2016/679',
                     description='EU regulation on data protection and privacy')
        session.commit()

        # Create comprehensive compliance requirements for ISO 27001
        iso_reqs = [
            {'requirement_id': 'A.5.1.1', 'title': 'Policies for information security', 
             'description': 'A set of policies for information security shall be defined, approved by management, published and communicated to employees and relevant external parties.', 
             'category': 'Information Security Policies'},
            
            {'requirement_id': 'A.5.1.2', 'title': 'Review of the policies for information security', 
             'description': 'The policies for information security shall be reviewed at planned intervals or if significant changes occur to ensure their continuing suitability, adequacy and effectiveness.', 
             'category': 'Information Security Policies'},
            
            {'requirement_id': 'A.6.1.1', 'title': 'Information security roles and responsibilities', 
             'description': 'All information security responsibilities shall be defined and allocated.', 
             'category': 'Organization of Information Security'},
            
            {'requirement_id': 'A.6.1.2', 'title': 'Segregation of duties', 
             'description': 'Conflicting duties and areas of responsibility shall be segregated to reduce opportunities for unauthorized or unintentional modification or misuse of the organization\'s assets.', 
             'category': 'Organization of Information Security'},
            
            {'requirement_id': 'A.7.1.1', 'title': 'Screening', 
             'description': 'Background verification checks on all candidates for employment shall be carried out in accordance with relevant laws, regulations and ethics and shall be proportional to the business requirements, the classification of the information to be accessed and the perceived risks.', 
             'category': 'Human Resource Security'},
            
            {'requirement_id': 'A.7.2.1', 'title': 'Management responsibilities', 
             'description': 'Management shall require all employees and contractors to apply information security in accordance with the established policies and procedures of the organization.', 
             'category': 'Human Resource Security'},
            
            {'requirement_id': 'A.8.1.1', 'title': 'Inventory of assets', 
             'description': 'Assets associated with information and information processing facilities shall be identified and an inventory of these assets shall be drawn up and maintained.', 
             'category': 'Asset Management'},
            
            {'requirement_id': 'A.8.1.2', 'title': 'Ownership of assets', 
             'description': 'Assets maintained in the inventory shall be owned.', 
             'category': 'Asset Management'},
            
            {'requirement_id': 'A.9.1.1', 'title': 'Access control policy', 
             'description': 'An access control policy shall be established, documented and reviewed based on business and information security requirements.', 
             'category': 'Access Control'},
            
            {'requirement_id': 'A.9.2.1', 'title': 'User registration and de-registration', 
             'description': 'A formal user registration and de-registration process shall be implemented to enable assignment of access rights.', 
             'category': 'Access Control'}
        ]
        
        for r in iso_reqs:
            upsert(session, ComplianceRequirement, 
                  {'requirement_id': r['requirement_id']}, 
                  title=r['title'], 
                  description=r.get('description'),
                  category=r.get('category'),
                  standard=iso)
        
        # Create compliance requirements for PCI DSS
        pci_reqs = [
            {'requirement_id': '1.1.1', 'title': 'Establish and implement firewall configuration standards', 
             'description': 'Processes and mechanisms for protecting system components from untrusted networks are defined and documented.', 
             'category': 'Build and Maintain a Secure Network'},
            
            {'requirement_id': '2.1.1', 'title': 'Change default passwords', 
             'description': 'Vendor-supplied defaults and other security parameters are managed and maintained.', 
             'category': 'Build and Maintain a Secure Network'},
            
            {'requirement_id': '3.2.1', 'title': 'Do not store sensitive authentication data', 
             'description': 'Account data storage is kept to a minimum.', 
             'category': 'Protect Account Data'},
            
            {'requirement_id': '4.1.1', 'title': 'Use strong cryptography and security protocols', 
             'description': 'Processes and mechanisms for protecting cardholder data with strong cryptography during transmission are defined and understood.', 
             'category': 'Protect Account Data'},
            
            {'requirement_id': '8.2.1', 'title': 'User identification and authentication', 
             'description': 'User identification and related accounts for users and administrators are strictly managed.', 
             'category': 'Identify and Authenticate Access'}
        ]
        
        for r in pci_reqs:
            upsert(session, ComplianceRequirement, 
                  {'requirement_id': r['requirement_id']}, 
                  title=r['title'], 
                  description=r.get('description'),
                  category=r.get('category'),
                  standard=pci)
        session.commit()

        # Create sample vendors with varied compliance metrics
        vendor_data = [
            {
                'name': 'TechCorp Systems',
                'description': 'Enterprise software solutions provider',
                'category': 'software_provider',
                'contact_email': 'compliance@techcorp.com',
                'website': 'https://techcorp.example.com',
                'risk_level': 'medium',
                'compliance_rate': Decimal('85.50'),
                'compliant_controls': 17,
                'non_compliant_controls': 3,
                'last_compliance_check': date.today() - timedelta(days=15)
            },
            {
                'name': 'SecureNet Solutions',
                'description': 'Cybersecurity and network infrastructure',
                'category': 'security_vendor',
                'contact_email': 'security@securenet.com',
                'website': 'https://securenet.example.com',
                'risk_level': 'low',
                'compliance_rate': Decimal('95.00'),
                'compliant_controls': 19,
                'non_compliant_controls': 1,
                'last_compliance_check': date.today() - timedelta(days=10)
            },
            {
                'name': 'CloudScale Inc',
                'description': 'Cloud infrastructure and services',
                'category': 'cloud_service',
                'contact_email': 'compliance@cloudscale.com',
                'website': 'https://cloudscale.example.com',
                'risk_level': 'medium',
                'compliance_rate': Decimal('72.00'),
                'compliant_controls': 14,
                'non_compliant_controls': 6,
                'last_compliance_check': date.today() - timedelta(days=30)
            },
            {
                'name': 'DataVault Pro',
                'description': 'Data storage and backup solutions',
                'category': 'data_processor',
                'contact_email': 'info@datavault.com',
                'website': 'https://datavault.example.com',
                'risk_level': 'high',
                'compliance_rate': Decimal('60.00'),
                'compliant_controls': 12,
                'non_compliant_controls': 8,
                'last_compliance_check': date.today() - timedelta(days=45)
            }
        ]
        
        vendors = []
        for v_data in vendor_data:
            v = upsert(session, Vendor, {'name': v_data['name']}, **v_data)
            vendors.append(v)
        session.commit()

        # Create assignments for different vendors and standards
        assignments_data = [
            {
                'name': 'Q4 2024 ISO 27001 Assessment - TechCorp',
                'description': 'Quarterly ISO 27001 compliance assessment for TechCorp Systems',
                'vendor': vendors[0],
                'standard': iso,
                'status': 'in_progress',
                'due_date': date(2024, 12, 31)
            },
            {
                'name': 'Q1 2025 PCI DSS Assessment - SecureNet',
                'description': 'PCI DSS v4.0 compliance review for SecureNet Solutions',
                'vendor': vendors[1],
                'standard': pci,
                'status': 'open',
                'due_date': date(2025, 3, 31)
            },
            {
                'name': 'Annual ISO 27001 Review - CloudScale',
                'description': 'Annual comprehensive ISO 27001 assessment',
                'vendor': vendors[2],
                'standard': iso,
                'status': 'open',
                'due_date': date(2025, 6, 30)
            }
        ]
        
        assignments = []
        for a_data in assignments_data:
            a = upsert(session, Assignment, 
                      {'name': a_data['name']}, 
                      description=a_data['description'],
                      vendor=a_data['vendor'],
                      standard=a_data['standard'],
                      status=a_data['status'],
                      due_date=a_data['due_date'])
            assignments.append(a)
        session.commit()

        # Create assessment rows for TechCorp ISO assignment with varied compliance statuses
        iso_requirements = session.query(ComplianceRequirement).filter(
            ComplianceRequirement.standard_id == iso.id
        ).all()
        
        assessment_statuses = [
            ('implemented', True, 'Fully compliant. Policy documents reviewed and approved by CISO.', 'John Smith'),
            ('implemented', True, 'All policies reviewed quarterly. Last review: Nov 2024.', 'Jane Doe'),
            ('implemented', True, 'Roles documented in security charter. Responsibilities assigned to security team.', 'John Smith'),
            ('partiallyImplemented', False, 'Segregation defined but not enforced in all systems. Remediation in progress.', 'Mike Johnson'),
            ('implemented', True, 'Background checks conducted for all new hires. Process documented.', 'HR Team'),
            ('implemented', True, 'Security awareness training mandatory for all employees and contractors.', 'Training Dept'),
            ('implemented', True, 'Asset inventory maintained in CMDB. Updated weekly.', 'IT Operations'),
            ('implemented', True, 'All assets have designated owners. Ownership review process in place.', 'IT Operations'),
            ('notImplemented', False, 'Access control policy exists but needs update to reflect current business requirements.', 'Security Team'),
            ('partiallyImplemented', False, 'User registration process automated. De-registration process needs improvement.', 'IT Support')
        ]
        
        for i, req in enumerate(iso_requirements):
            if i < len(assessment_statuses):
                status, compliant, remark, poc = assessment_statuses[i]
            else:
                status, compliant, remark, poc = 'notImplemented', False, 'Pending assessment', 'TBD'
            
            a = Assessment(
                vendor=vendors[0],
                assignment=assignments[0],
                compliance_requirement=req,
                control_identifier=req.requirement_id,
                compliant=compliant,
                remark=remark,
                poc=poc,
                status=status
            )
            session.add(a)
        
        # Create assessments for SecureNet PCI assignment
        pci_requirements = session.query(ComplianceRequirement).filter(
            ComplianceRequirement.standard_id == pci.id
        ).all()
        
        pci_assessment_statuses = [
            ('implemented', True, 'Firewall rules documented and reviewed monthly. Configuration standards maintained.', 'Network Team'),
            ('implemented', True, 'Default passwords changed on all systems. Password policy enforced.', 'Security Admin'),
            ('implemented', True, 'No sensitive authentication data stored. Cardholder data encrypted at rest.', 'Database Team'),
            ('implemented', True, 'TLS 1.2+ enforced for all cardholder data transmission. Certificates up to date.', 'Network Security'),
            ('partiallyImplemented', False, 'MFA implemented for admin access. User access MFA rollout in progress.', 'IAM Team')
        ]
        
        for i, req in enumerate(pci_requirements):
            if i < len(pci_assessment_statuses):
                status, compliant, remark, poc = pci_assessment_statuses[i]
            else:
                status, compliant, remark, poc = 'notImplemented', False, 'Assessment scheduled', 'TBD'
            
            a = Assessment(
                vendor=vendors[1],
                assignment=assignments[1],
                compliance_requirement=req,
                control_identifier=req.requirement_id,
                compliant=compliant,
                remark=remark,
                poc=poc,
                status=status
            )
            session.add(a)
        session.commit()

        print('✅ Seeding complete!')
        print(f'   - Created 4 compliance standards (ISO 27001, PCI DSS, SOC2, GDPR)')
        print(f'   - Created {len(iso_reqs)} ISO 27001 requirements')
        print(f'   - Created {len(pci_reqs)} PCI DSS requirements')
        print(f'   - Created {len(vendors)} vendors with compliance metrics')
        print(f'   - Created {len(assignments)} assignments')
        print(f'   - Created assessments with varied compliance statuses')
        
    except Exception as e:
        session.rollback()
        print('❌ Seeding error:', e)
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    seed()
