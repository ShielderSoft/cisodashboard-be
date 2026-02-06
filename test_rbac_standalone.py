"""
Standalone RBAC Tests - Tests RBAC logic without importing full app
"""
from enum import Enum
from typing import List, Optional


# Copy of UserRole enum for testing
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CISO = "CISO"
    INFOSEC_MANAGER = "INFOSEC_MANAGER"
    EXTERNAL_AUDITOR = "EXTERNAL_AUDITOR"
    INTERNAL_AUDITOR = "INTERNAL_AUDITOR"
    SECURITY_ANALYST = "SECURITY_ANALYST"
    VIEWER = "VIEWER"


# Copy of RBAC logic for testing
ROLE_HIERARCHY = {
    UserRole.ADMIN: [
        UserRole.ADMIN,
        UserRole.CISO,
        UserRole.INFOSEC_MANAGER,
        UserRole.EXTERNAL_AUDITOR,
        UserRole.INTERNAL_AUDITOR,
        UserRole.SECURITY_ANALYST,
        UserRole.VIEWER,
    ],
    UserRole.CISO: [
        UserRole.CISO,
        UserRole.INFOSEC_MANAGER,
        UserRole.SECURITY_ANALYST,
        UserRole.VIEWER,
    ],
    UserRole.INFOSEC_MANAGER: [
        UserRole.INFOSEC_MANAGER,
        UserRole.SECURITY_ANALYST,
        UserRole.VIEWER,
    ],
    UserRole.EXTERNAL_AUDITOR: [UserRole.EXTERNAL_AUDITOR, UserRole.VIEWER],
    UserRole.INTERNAL_AUDITOR: [UserRole.INTERNAL_AUDITOR, UserRole.VIEWER],
    UserRole.SECURITY_ANALYST: [UserRole.SECURITY_ANALYST, UserRole.VIEWER],
    UserRole.VIEWER: [UserRole.VIEWER],
}

ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "users": ["create", "read", "update", "delete"],
        "applications": ["create", "read", "update", "delete"],
        "vulnerabilities": ["create", "read", "update", "delete"],
        "compliance": ["create", "read", "update", "delete"],
        "vendors": ["create", "read", "update", "delete"],
        "exceptions": ["create", "read", "update", "delete", "approve"],
        "reports": ["create", "read", "update", "delete"],
        "audit": ["create", "read", "update", "delete"],
        "settings": ["create", "read", "update", "delete"],
    },
    UserRole.CISO: {
        "applications": ["read", "update"],
        "vulnerabilities": ["read", "update"],
        "compliance": ["read", "update"],
        "vendors": ["read", "update"],
        "exceptions": ["read", "approve"],
        "reports": ["create", "read", "update"],
        "audit": ["read"],
        "settings": ["read"],
    },
    UserRole.INFOSEC_MANAGER: {
        "applications": ["create", "read", "update"],
        "vulnerabilities": ["create", "read", "update"],
        "compliance": ["read", "update"],
        "vendors": ["read", "update"],
        "exceptions": ["create", "read"],
        "reports": ["read"],
    },
    UserRole.EXTERNAL_AUDITOR: {
        "applications": ["read"],
        "vulnerabilities": ["read"],
        "compliance": ["read"],
        "vendors": ["read"],
        "exceptions": ["read"],
        "reports": ["read"],
        "audit": ["read"],
    },
    UserRole.INTERNAL_AUDITOR: {
        "applications": ["read"],
        "vulnerabilities": ["read"],
        "compliance": ["read"],
        "vendors": ["read"],
        "exceptions": ["read"],
        "reports": ["create", "read"],
        "audit": ["create", "read"],
    },
    UserRole.SECURITY_ANALYST: {
        "applications": ["read", "update"],
        "vulnerabilities": ["create", "read", "update"],
        "compliance": ["read"],
        "vendors": ["read"],
        "exceptions": ["create", "read"],
        "reports": ["read"],
    },
    UserRole.VIEWER: {
        "applications": ["read"],
        "vulnerabilities": ["read"],
        "compliance": ["read"],
        "vendors": ["read"],
        "exceptions": ["read"],
        "reports": ["read"],
        "audit": ["read"],
    },
}


class MockUser:
    def __init__(self, role: UserRole):
        self.role = role


def check_role(user: MockUser, required_roles: List[UserRole]) -> bool:
    """Check if user has any of the required roles"""
    if not user or not user.role:
        return False
    
    user_role = user.role
    if user_role not in ROLE_HIERARCHY:
        return False
    
    allowed_roles = ROLE_HIERARCHY[user_role]
    
    return any(role in allowed_roles for role in required_roles)


def check_permission(user: MockUser, resource: str, action: str) -> bool:
    """Check if user has permission to perform action on resource"""
    if not user or not user.role:
        return False
    
    user_role = user.role
    if user_role not in ROLE_HIERARCHY:
        return False
    
    allowed_roles = ROLE_HIERARCHY[user_role]
    
    for role in allowed_roles:
        if role in ROLE_PERMISSIONS:
            role_perms = ROLE_PERMISSIONS[role]
            if resource in role_perms and action in role_perms[resource]:
                return True
    
    return False


# Test functions
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
    print("\n" + "=" * 60)
    print("🧪 RBAC COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")
    
    # Role hierarchy tests
    print("📋 Testing Role Hierarchy:")
    print("-" * 60)
    test_admin_has_all_roles()
    test_ciso_role_hierarchy()
    test_infosec_manager_hierarchy()
    test_auditor_roles_independent()
    test_viewer_lowest_access()
    
    # Permission tests
    print("\n🔐 Testing Permissions:")
    print("-" * 60)
    test_admin_full_permissions()
    test_ciso_permissions()
    test_infosec_manager_permissions()
    test_external_auditor_read_only()
    test_internal_auditor_can_create_reports()
    test_security_analyst_vulnerability_permissions()
    test_viewer_read_only_all()
    
    # Specific permission tests
    print("\n⚡ Testing Specific Permissions:")
    print("-" * 60)
    test_only_admin_can_delete_users()
    test_exception_approval_permissions()
    
    print("\n" + "=" * 60)
    print("✅ All 14 RBAC tests passed successfully! 🎉")
    print("=" * 60 + "\n")
    
    # Print summary
    print("📊 Test Summary:")
    print("-" * 60)
    print(f"✓ Role Hierarchy Tests: 5/5")
    print(f"✓ Permission Tests: 7/7")
    print(f"✓ Specific Permission Tests: 2/2")
    print(f"✓ Total Tests Passed: 14/14")
    print("=" * 60 + "\n")
