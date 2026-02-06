"""
Simple RBAC tests without database dependencies
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.rbac import check_role, check_permission, ROLE_HIERARCHY, ROLE_PERMISSIONS
from app.models.models import UserRole


# Mock user class for testing
class MockUser:
    def __init__(self, role):
        self.role = role


def test_admin_has_all_roles():
    """Admin should have access to all roles"""
    user = MockUser(UserRole.ADMIN)
    
    assert check_role(user, [UserRole.ADMIN])
    assert check_role(user, [UserRole.CISO])
    assert check_role(user, [UserRole.INFOSEC_MANAGER])
    assert check_role(user, [UserRole.EXTERNAL_AUDITOR])
    assert check_role(user, [UserRole.INTERNAL_AUDITOR])
    assert check_role(user, [UserRole.SECURITY_ANALYST])
    assert check_role(user, [UserRole.VIEWER])
    print("✅ test_admin_has_all_roles passed")


def test_ciso_role_hierarchy():
    """CISO should have access to InfoSec Manager, Security Analyst, and Viewer"""
    user = MockUser(UserRole.CISO)
    
    assert check_role(user, [UserRole.CISO])
    assert check_role(user, [UserRole.INFOSEC_MANAGER])
    assert check_role(user, [UserRole.SECURITY_ANALYST])
    assert check_role(user, [UserRole.VIEWER])
    assert not check_role(user, [UserRole.ADMIN])
    assert not check_role(user, [UserRole.EXTERNAL_AUDITOR])
    print("✅ test_ciso_role_hierarchy passed")


def test_infosec_manager_hierarchy():
    """InfoSec Manager should have limited access"""
    user = MockUser(UserRole.INFOSEC_MANAGER)
    
    assert check_role(user, [UserRole.INFOSEC_MANAGER])
    assert check_role(user, [UserRole.SECURITY_ANALYST])
    assert check_role(user, [UserRole.VIEWER])
    assert not check_role(user, [UserRole.ADMIN])
    assert not check_role(user, [UserRole.CISO])
    print("✅ test_infosec_manager_hierarchy passed")


def test_auditor_roles_independent():
    """External and Internal Auditors should be independent"""
    external_user = MockUser(UserRole.EXTERNAL_AUDITOR)
    internal_user = MockUser(UserRole.INTERNAL_AUDITOR)
    
    assert check_role(external_user, [UserRole.EXTERNAL_AUDITOR])
    assert check_role(external_user, [UserRole.VIEWER])
    assert not check_role(external_user, [UserRole.INTERNAL_AUDITOR])
    
    assert check_role(internal_user, [UserRole.INTERNAL_AUDITOR])
    assert check_role(internal_user, [UserRole.VIEWER])
    assert not check_role(internal_user, [UserRole.EXTERNAL_AUDITOR])
    print("✅ test_auditor_roles_independent passed")


def test_viewer_lowest_access():
    """Viewer should only have viewer access"""
    user = MockUser(UserRole.VIEWER)
    
    assert check_role(user, [UserRole.VIEWER])
    assert not check_role(user, [UserRole.SECURITY_ANALYST])
    assert not check_role(user, [UserRole.ADMIN])
    print("✅ test_viewer_lowest_access passed")


def test_admin_full_permissions():
    """Admin should have all permissions"""
    user = MockUser(UserRole.ADMIN)
    
    assert check_permission(user, "users", "create")
    assert check_permission(user, "users", "delete")
    assert check_permission(user, "vulnerabilities", "create")
    assert check_permission(user, "exceptions", "approve")
    assert check_permission(user, "settings", "update")
    print("✅ test_admin_full_permissions passed")


def test_ciso_permissions():
    """CISO should have read/update but not create/delete for most resources"""
    user = MockUser(UserRole.CISO)
    
    # Can read and update
    assert check_permission(user, "applications", "read")
    assert check_permission(user, "applications", "update")
    assert check_permission(user, "vulnerabilities", "read")
    assert check_permission(user, "vulnerabilities", "update")
    
    # Cannot delete
    assert not check_permission(user, "applications", "delete")
    assert not check_permission(user, "vulnerabilities", "delete")
    
    # Can approve exceptions
    assert check_permission(user, "exceptions", "approve")
    
    # Can create reports but not delete
    assert check_permission(user, "reports", "create")
    assert not check_permission(user, "reports", "delete")
    print("✅ test_ciso_permissions passed")


def test_infosec_manager_permissions():
    """InfoSec Manager should have CRUD on vulnerabilities and applications"""
    user = MockUser(UserRole.INFOSEC_MANAGER)
    
    # Can create, read, update
    assert check_permission(user, "applications", "create")
    assert check_permission(user, "applications", "read")
    assert check_permission(user, "applications", "update")
    assert check_permission(user, "vulnerabilities", "create")
    
    # Cannot delete or manage users
    assert not check_permission(user, "applications", "delete")
    assert not check_permission(user, "users", "create")
    assert not check_permission(user, "users", "read")
    print("✅ test_infosec_manager_permissions passed")


def test_external_auditor_read_only():
    """External Auditor should be read-only"""
    user = MockUser(UserRole.EXTERNAL_AUDITOR)
    
    # Can read
    assert check_permission(user, "applications", "read")
    assert check_permission(user, "vulnerabilities", "read")
    assert check_permission(user, "compliance", "read")
    assert check_permission(user, "audit", "read")
    
    # Cannot create, update, or delete
    assert not check_permission(user, "applications", "create")
    assert not check_permission(user, "applications", "update")
    assert not check_permission(user, "applications", "delete")
    assert not check_permission(user, "vulnerabilities", "create")
    assert not check_permission(user, "exceptions", "approve")
    print("✅ test_external_auditor_read_only passed")


def test_internal_auditor_can_create_reports():
    """Internal Auditor should be able to create reports and audits"""
    user = MockUser(UserRole.INTERNAL_AUDITOR)
    
    # Can create reports and audits
    assert check_permission(user, "reports", "create")
    assert check_permission(user, "reports", "read")
    assert check_permission(user, "audit", "create")
    assert check_permission(user, "audit", "read")
    
    # Cannot modify other resources
    assert not check_permission(user, "vulnerabilities", "create")
    assert not check_permission(user, "applications", "update")
    print("✅ test_internal_auditor_can_create_reports passed")


def test_security_analyst_vulnerability_permissions():
    """Security Analyst should have full access to vulnerabilities"""
    user = MockUser(UserRole.SECURITY_ANALYST)
    
    # Full CRUD on vulnerabilities
    assert check_permission(user, "vulnerabilities", "create")
    assert check_permission(user, "vulnerabilities", "read")
    assert check_permission(user, "vulnerabilities", "update")
    
    # Limited on applications
    assert check_permission(user, "applications", "read")
    assert check_permission(user, "applications", "update")
    assert not check_permission(user, "applications", "create")
    assert not check_permission(user, "applications", "delete")
    
    # Cannot approve exceptions
    assert not check_permission(user, "exceptions", "approve")
    print("✅ test_security_analyst_vulnerability_permissions passed")


def test_viewer_read_only_all():
    """Viewer should have read-only access to everything"""
    user = MockUser(UserRole.VIEWER)
    
    # Can read everything
    assert check_permission(user, "applications", "read")
    assert check_permission(user, "vulnerabilities", "read")
    assert check_permission(user, "compliance", "read")
    assert check_permission(user, "reports", "read")
    
    # Cannot modify anything
    assert not check_permission(user, "applications", "create")
    assert not check_permission(user, "vulnerabilities", "update")
    assert not check_permission(user, "reports", "create")
    assert not check_permission(user, "exceptions", "approve")
    print("✅ test_viewer_read_only_all passed")


def test_only_admin_can_delete_users():
    """Only admin should be able to delete users"""
    admin = MockUser(UserRole.ADMIN)
    ciso = MockUser(UserRole.CISO)
    manager = MockUser(UserRole.INFOSEC_MANAGER)
    
    assert check_permission(admin, "users", "delete")
    assert not check_permission(ciso, "users", "delete")
    assert not check_permission(manager, "users", "delete")
    print("✅ test_only_admin_can_delete_users passed")


def test_exception_approval_permissions():
    """Only ADMIN and CISO should be able to approve exceptions"""
    admin = MockUser(UserRole.ADMIN)
    ciso = MockUser(UserRole.CISO)
    manager = MockUser(UserRole.INFOSEC_MANAGER)
    analyst = MockUser(UserRole.SECURITY_ANALYST)
    
    assert check_permission(admin, "exceptions", "approve")
    assert check_permission(ciso, "exceptions", "approve")
    assert not check_permission(manager, "exceptions", "approve")
    assert not check_permission(analyst, "exceptions", "approve")
    print("✅ test_exception_approval_permissions passed")


if __name__ == "__main__":
    print("\n🧪 Running RBAC Tests...\n")
    
    # Role hierarchy tests
    print("📋 Testing Role Hierarchy:")
    test_admin_has_all_roles()
    test_ciso_role_hierarchy()
    test_infosec_manager_hierarchy()
    test_auditor_roles_independent()
    test_viewer_lowest_access()
    
    # Permission tests
    print("\n🔐 Testing Permissions:")
    test_admin_full_permissions()
    test_ciso_permissions()
    test_infosec_manager_permissions()
    test_external_auditor_read_only()
    test_internal_auditor_can_create_reports()
    test_security_analyst_vulnerability_permissions()
    test_viewer_read_only_all()
    
    # Specific permission tests
    print("\n⚡ Testing Specific Permissions:")
    test_only_admin_can_delete_users()
    test_exception_approval_permissions()
    
    print("\n✅ All RBAC tests passed successfully! 🎉\n")
