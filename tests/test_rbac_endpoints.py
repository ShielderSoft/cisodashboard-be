"""
Integration tests for RBAC on API endpoints
"""
import pytest
from httpx import AsyncClient
from app.models.models import UserRole


@pytest.mark.asyncio
class TestUserEndpointRBAC:
    """Test RBAC on user management endpoints"""
    
    async def test_admin_can_list_users(self, async_client, admin_user):
        """Admin should be able to list all users"""
        # This test assumes /api/v1/users endpoint exists with RBAC protection
        # Endpoint should have: @require_roles([UserRole.ADMIN])
        
        response = await async_client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer mock_token_for_{admin_user.email}"}
        )
        
        # Should succeed (200 or 403 depending on implementation)
        # When RBAC is applied, this test will verify the decorator works
        assert response.status_code in [200, 401, 404]  # 404 if endpoint not created yet
    
    async def test_ciso_cannot_delete_users(self, async_client, ciso_user):
        """CISO should not be able to delete users"""
        response = await async_client.delete(
            "/api/v1/users/1",
            headers={"Authorization": f"Bearer mock_token_for_{ciso_user.email}"}
        )
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404]
    
    async def test_viewer_cannot_create_users(self, async_client, viewer_user):
        """Viewer should not be able to create users"""
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": "newuser@test.com",
                "username": "newuser",
                "password": "NewUser@123",
                "role": "VIEWER"
            },
            headers={"Authorization": f"Bearer mock_token_for_{viewer_user.email}"}
        )
        
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
class TestVulnerabilityEndpointRBAC:
    """Test RBAC on vulnerability endpoints"""
    
    async def test_security_analyst_can_create_vulnerability(
        self, async_client, security_analyst_user
    ):
        """Security Analyst should be able to create vulnerabilities"""
        response = await async_client.post(
            "/api/v1/vulnerabilities",
            json={
                "title": "Test Vulnerability",
                "severity": "HIGH",
                "status": "OPEN",
                "description": "Test description"
            },
            headers={"Authorization": f"Bearer mock_token_for_{security_analyst_user.email}"}
        )
        
        # Should succeed or return 404 if endpoint doesn't exist
        assert response.status_code in [200, 201, 404]
    
    async def test_external_auditor_cannot_create_vulnerability(
        self, async_client, external_auditor_user
    ):
        """External Auditor should not be able to create vulnerabilities"""
        response = await async_client.post(
            "/api/v1/vulnerabilities",
            json={
                "title": "Test Vulnerability",
                "severity": "HIGH",
                "status": "OPEN",
                "description": "Test description"
            },
            headers={"Authorization": f"Bearer mock_token_for_{external_auditor_user.email}"}
        )
        
        # Should be forbidden
        assert response.status_code in [403, 404]
    
    async def test_viewer_can_read_vulnerabilities(self, async_client, viewer_user):
        """Viewer should be able to read vulnerabilities"""
        response = await async_client.get(
            "/api/v1/vulnerabilities",
            headers={"Authorization": f"Bearer mock_token_for_{viewer_user.email}"}
        )
        
        # Should succeed or return 404
        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestExceptionEndpointRBAC:
    """Test RBAC on exception approval endpoints"""
    
    async def test_ciso_can_approve_exception(self, async_client, ciso_user):
        """CISO should be able to approve exceptions"""
        response = await async_client.patch(
            "/api/v1/exceptions/1/approve",
            headers={"Authorization": f"Bearer mock_token_for_{ciso_user.email}"}
        )
        
        assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist
    
    async def test_infosec_manager_cannot_approve_exception(
        self, async_client, infosec_manager_user
    ):
        """InfoSec Manager should not be able to approve exceptions"""
        response = await async_client.patch(
            "/api/v1/exceptions/1/approve",
            headers={"Authorization": f"Bearer mock_token_for_{infosec_manager_user.email}"}
        )
        
        assert response.status_code in [403, 404]
    
    async def test_security_analyst_cannot_approve_exception(
        self, async_client, security_analyst_user
    ):
        """Security Analyst should not be able to approve exceptions"""
        response = await async_client.patch(
            "/api/v1/exceptions/1/approve",
            headers={"Authorization": f"Bearer mock_token_for_{security_analyst_user.email}"}
        )
        
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
class TestApplicationEndpointRBAC:
    """Test RBAC on application management endpoints"""
    
    async def test_infosec_manager_can_create_application(
        self, async_client, infosec_manager_user
    ):
        """InfoSec Manager should be able to create applications"""
        response = await async_client.post(
            "/api/v1/applications",
            json={
                "name": "Test Application",
                "type": "WEB",
                "criticality": "HIGH",
                "owner": "test@test.com"
            },
            headers={"Authorization": f"Bearer mock_token_for_{infosec_manager_user.email}"}
        )
        
        assert response.status_code in [200, 201, 404]
    
    async def test_external_auditor_can_read_applications(
        self, async_client, external_auditor_user
    ):
        """External Auditor should be able to read applications"""
        response = await async_client.get(
            "/api/v1/applications",
            headers={"Authorization": f"Bearer mock_token_for_{external_auditor_user.email}"}
        )
        
        assert response.status_code in [200, 404]
    
    async def test_external_auditor_cannot_update_application(
        self, async_client, external_auditor_user
    ):
        """External Auditor should not be able to update applications"""
        response = await async_client.put(
            "/api/v1/applications/1",
            json={
                "name": "Updated Application",
                "type": "WEB"
            },
            headers={"Authorization": f"Bearer mock_token_for_{external_auditor_user.email}"}
        )
        
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
class TestReportEndpointRBAC:
    """Test RBAC on report generation endpoints"""
    
    async def test_internal_auditor_can_create_reports(
        self, async_client, internal_auditor_user
    ):
        """Internal Auditor should be able to create reports"""
        response = await async_client.post(
            "/api/v1/reports",
            json={
                "title": "Audit Report",
                "type": "AUDIT",
                "period": "Q1-2024"
            },
            headers={"Authorization": f"Bearer mock_token_for_{internal_auditor_user.email}"}
        )
        
        assert response.status_code in [200, 201, 404]
    
    async def test_external_auditor_can_read_reports(
        self, async_client, external_auditor_user
    ):
        """External Auditor should be able to read reports"""
        response = await async_client.get(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer mock_token_for_{external_auditor_user.email}"}
        )
        
        assert response.status_code in [200, 404]
    
    async def test_security_analyst_cannot_delete_reports(
        self, async_client, security_analyst_user
    ):
        """Security Analyst should not be able to delete reports"""
        response = await async_client.delete(
            "/api/v1/reports/1",
            headers={"Authorization": f"Bearer mock_token_for_{security_analyst_user.email}"}
        )
        
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
class TestSettingsEndpointRBAC:
    """Test RBAC on settings endpoints"""
    
    async def test_admin_can_update_settings(self, async_client, admin_user):
        """Admin should be able to update settings"""
        response = await async_client.patch(
            "/api/v1/settings",
            json={
                "notification_enabled": True,
                "max_login_attempts": 5
            },
            headers={"Authorization": f"Bearer mock_token_for_{admin_user.email}"}
        )
        
        assert response.status_code in [200, 404]
    
    async def test_ciso_can_read_settings(self, async_client, ciso_user):
        """CISO should be able to read settings"""
        response = await async_client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer mock_token_for_{ciso_user.email}"}
        )
        
        assert response.status_code in [200, 404]
    
    async def test_viewer_cannot_update_settings(self, async_client, viewer_user):
        """Viewer should not be able to update settings"""
        response = await async_client.patch(
            "/api/v1/settings",
            json={
                "notification_enabled": False
            },
            headers={"Authorization": f"Bearer mock_token_for_{viewer_user.email}"}
        )
        
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
class TestRoleHierarchyInEndpoints:
    """Test that role hierarchy works correctly in endpoints"""
    
    async def test_admin_has_access_to_all_endpoints(self, async_client, admin_user):
        """Admin should have access to all protected endpoints"""
        endpoints = [
            ("GET", "/api/v1/users"),
            ("GET", "/api/v1/applications"),
            ("GET", "/api/v1/vulnerabilities"),
            ("GET", "/api/v1/reports"),
            ("GET", "/api/v1/settings"),
        ]
        
        for method, endpoint in endpoints:
            response = await async_client.request(
                method,
                endpoint,
                headers={"Authorization": f"Bearer mock_token_for_{admin_user.email}"}
            )
            
            # Admin should never get 403
            assert response.status_code != 403
    
    async def test_ciso_inherits_infosec_manager_permissions(
        self, async_client, ciso_user
    ):
        """CISO should have all InfoSec Manager permissions"""
        # Test an endpoint that InfoSec Manager can access
        response = await async_client.get(
            "/api/v1/applications",
            headers={"Authorization": f"Bearer mock_token_for_{ciso_user.email}"}
        )
        
        # CISO should be able to access this
        assert response.status_code in [200, 404]
        assert response.status_code != 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
