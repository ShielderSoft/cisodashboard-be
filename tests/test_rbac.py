"""
Tests for Role-Based Access Control (RBAC)
"""
import pytest
from app.core.rbac import (
    check_role,
    check_permission,
    ROLE_HIERARCHY,
    ROLE_PERMISSIONS,
)
from app.models.models import User, UserRole


class TestRoleHierarchy:
    """Test role hierarchy and inheritance"""
    
    def test_admin_has_all_roles(self):
        """Admin should have access to all roles"""
        user = User(role=UserRole.ADMIN)
        
        assert check_role(user, [UserRole.ADMIN])
        assert check_role(user, [UserRole.CISO])
        assert check_role(user, [UserRole.INFOSEC_MANAGER])
        assert check_role(user, [UserRole.EXTERNAL_AUDITOR])
        assert check_role(user, [UserRole.INTERNAL_AUDITOR])
        assert check_role(user, [UserRole.SECURITY_ANALYST])
        assert check_role(user, [UserRole.VIEWER])
    
    def test_ciso_role_hierarchy(self):
        """CISO should have access to InfoSec Manager, Security Analyst, and Viewer"""
        user = User(role=UserRole.CISO)
        
        assert check_role(user, [UserRole.CISO])
        assert check_role(user, [UserRole.INFOSEC_MANAGER])
        assert check_role(user, [UserRole.SECURITY_ANALYST])
        assert check_role(user, [UserRole.VIEWER])
        assert not check_role(user, [UserRole.ADMIN])
        assert not check_role(user, [UserRole.EXTERNAL_AUDITOR])
    
    def test_infosec_manager_role_hierarchy(self):
        """InfoSec Manager should have limited access"""
        user = User(role=UserRole.INFOSEC_MANAGER)
        
        assert check_role(user, [UserRole.INFOSEC_MANAGER])
        assert check_role(user, [UserRole.SECURITY_ANALYST])
        assert check_role(user, [UserRole.VIEWER])
        assert not check_role(user, [UserRole.ADMIN])
        assert not check_role(user, [UserRole.CISO])
    
    def test_auditor_roles_independent(self):
        """External and Internal Auditors should be independent"""
        external_user = User(role=UserRole.EXTERNAL_AUDITOR)
        internal_user = User(role=UserRole.INTERNAL_AUDITOR)
        
        assert check_role(external_user, [UserRole.EXTERNAL_AUDITOR])
        assert check_role(external_user, [UserRole.VIEWER])
        assert not check_role(external_user, [UserRole.INTERNAL_AUDITOR])
        
        assert check_role(internal_user, [UserRole.INTERNAL_AUDITOR])
        assert check_role(internal_user, [UserRole.VIEWER])
        assert not check_role(internal_user, [UserRole.EXTERNAL_AUDITOR])
    
    def test_viewer_lowest_access(self):
        """Viewer should only have viewer access"""
        user = User(role=UserRole.VIEWER)
        
        assert check_role(user, [UserRole.VIEWER])
        assert not check_role(user, [UserRole.SECURITY_ANALYST])
        assert not check_role(user, [UserRole.ADMIN])


class TestPermissions:
    """Test permission checks"""
    
    def test_admin_full_permissions(self):
        """Admin should have all permissions"""
        user = User(role=UserRole.ADMIN)
        
        # Test various resources
        assert check_permission(user, "users", "create")
        assert check_permission(user, "users", "delete")
        assert check_permission(user, "vulnerabilities", "create")
        assert check_permission(user, "exceptions", "approve")
        assert check_permission(user, "settings", "update")
    
    def test_ciso_permissions(self):
        """CISO should have read/update but not create/delete for most resources"""
        user = User(role=UserRole.CISO)
        
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
    
    def test_infosec_manager_permissions(self):
        """InfoSec Manager should have CRUD on vulnerabilities and applications"""
        user = User(role=UserRole.INFOSEC_MANAGER)
        
        # Can create, read, update
        assert check_permission(user, "applications", "create")
        assert check_permission(user, "applications", "read")
        assert check_permission(user, "applications", "update")
        assert check_permission(user, "vulnerabilities", "create")
        
        # Cannot delete or manage users
        assert not check_permission(user, "applications", "delete")
        assert not check_permission(user, "users", "create")
        assert not check_permission(user, "users", "read")
    
    def test_external_auditor_read_only(self):
        """External Auditor should be read-only"""
        user = User(role=UserRole.EXTERNAL_AUDITOR)
        
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
    
    def test_internal_auditor_can_create_reports(self):
        """Internal Auditor should be able to create reports and audits"""
        user = User(role=UserRole.INTERNAL_AUDITOR)
        
        # Can create reports and audits
        assert check_permission(user, "reports", "create")
        assert check_permission(user, "reports", "read")
        assert check_permission(user, "audit", "create")
        assert check_permission(user, "audit", "read")
        
        # Cannot modify other resources
        assert not check_permission(user, "vulnerabilities", "create")
        assert not check_permission(user, "applications", "update")
    
    def test_security_analyst_vulnerability_permissions(self):
        """Security Analyst should have full access to vulnerabilities"""
        user = User(role=UserRole.SECURITY_ANALYST)
        
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
    
    def test_viewer_read_only_all(self):
        """Viewer should have read-only access to everything"""
        user = User(role=UserRole.VIEWER)
        
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


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_user_without_role(self):
        """User without role should have no access"""
        user = User(role=None)
        
        assert not check_role(user, [UserRole.VIEWER])
        assert not check_permission(user, "applications", "read")
    
    def test_invalid_role_string(self):
        """Invalid role string should be handled gracefully"""
        user = User(role="INVALID_ROLE")
        
        # Should not crash, just return False
        assert not check_role(user, [UserRole.ADMIN])
        assert not check_permission(user, "applications", "read")
    
    def test_none_user(self):
        """None user should have no access"""
        assert not check_role(None, [UserRole.ADMIN])
        assert not check_permission(None, "applications", "read")
    
    def test_multiple_required_roles(self):
        """Check with multiple required roles (OR logic)"""
        ciso_user = User(role=UserRole.CISO)
        analyst_user = User(role=UserRole.SECURITY_ANALYST)
        viewer_user = User(role=UserRole.VIEWER)
        
        # CISO should match [ADMIN, CISO]
        assert check_role(ciso_user, [UserRole.ADMIN, UserRole.CISO])
        
        # Analyst should not match [ADMIN, CISO]
        assert not check_role(analyst_user, [UserRole.ADMIN, UserRole.CISO])
        
        # But should match [SECURITY_ANALYST, CISO]
        assert check_role(analyst_user, [UserRole.SECURITY_ANALYST, UserRole.CISO])
        
        # Viewer should not match restricted roles
        assert not check_role(viewer_user, [UserRole.ADMIN, UserRole.CISO])


class TestRolePermissionMatrix:
    """Test the complete permission matrix for consistency"""
    
    def test_all_roles_have_viewer_permissions(self):
        """All roles should have at least viewer permissions"""
        for role in UserRole:
            user = User(role=role)
            # Everyone should be able to read
            assert check_permission(user, "applications", "read")
            assert check_permission(user, "vulnerabilities", "read")
    
    def test_only_admin_can_delete_users(self):
        """Only admin should be able to delete users"""
        admin = User(role=UserRole.ADMIN)
        ciso = User(role=UserRole.CISO)
        manager = User(role=UserRole.INFOSEC_MANAGER)
        
        assert check_permission(admin, "users", "delete")
        assert not check_permission(ciso, "users", "delete")
        assert not check_permission(manager, "users", "delete")
    
    def test_exception_approval_permissions(self):
        """Only ADMIN and CISO should be able to approve exceptions"""
        admin = User(role=UserRole.ADMIN)
        ciso = User(role=UserRole.CISO)
        manager = User(role=UserRole.INFOSEC_MANAGER)
        analyst = User(role=UserRole.SECURITY_ANALYST)
        
        assert check_permission(admin, "exceptions", "approve")
        assert check_permission(ciso, "exceptions", "approve")
        assert not check_permission(manager, "exceptions", "approve")
        assert not check_permission(analyst, "exceptions", "approve")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
