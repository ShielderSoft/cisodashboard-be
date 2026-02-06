"""
Role-Based Access Control (RBAC) utilities and decorators
"""
from functools import wraps
from typing import List, Callable
from fastapi import HTTPException, status, Depends
from app.models.models import User, UserRole


# Define role hierarchy - higher roles inherit lower role permissions
ROLE_HIERARCHY = {
    UserRole.ADMIN: [
        UserRole.ADMIN,
        UserRole.CISO,
        UserRole.INFOSEC_MANAGER,
        UserRole.EXTERNAL_AUDITOR,
        UserRole.INTERNAL_AUDITOR,
        UserRole.SECURITY_ANALYST,
        UserRole.VIEWER
    ],
    UserRole.CISO: [
        UserRole.CISO,
        UserRole.INFOSEC_MANAGER,
        UserRole.SECURITY_ANALYST,
        UserRole.VIEWER
    ],
    UserRole.INFOSEC_MANAGER: [
        UserRole.INFOSEC_MANAGER,
        UserRole.SECURITY_ANALYST,
        UserRole.VIEWER
    ],
    UserRole.EXTERNAL_AUDITOR: [
        UserRole.EXTERNAL_AUDITOR,
        UserRole.VIEWER
    ],
    UserRole.INTERNAL_AUDITOR: [
        UserRole.INTERNAL_AUDITOR,
        UserRole.VIEWER
    ],
    UserRole.SECURITY_ANALYST: [
        UserRole.SECURITY_ANALYST,
        UserRole.VIEWER
    ],
    UserRole.VIEWER: [
        UserRole.VIEWER
    ]
}


# Define permissions for each role
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
        "settings": ["read", "update"],
    },
    UserRole.CISO: {
        "users": ["read"],
        "applications": ["read", "update"],
        "vulnerabilities": ["read", "update"],
        "compliance": ["read", "update"],
        "vendors": ["read", "update"],
        "exceptions": ["read", "approve"],
        "reports": ["create", "read"],
        "audit": ["read"],
        "settings": ["read"],
    },
    UserRole.INFOSEC_MANAGER: {
        "applications": ["create", "read", "update"],
        "vulnerabilities": ["create", "read", "update"],
        "compliance": ["read", "update"],
        "vendors": ["read", "update"],
        "exceptions": ["create", "read", "update"],
        "reports": ["create", "read"],
        "audit": ["read"],
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
        "audit": ["read"],
    },
    UserRole.VIEWER: {
        "applications": ["read"],
        "vulnerabilities": ["read"],
        "compliance": ["read"],
        "vendors": ["read"],
        "exceptions": ["read"],
        "reports": ["read"],
        "audit": ["read"],
    }
}


def check_role(user: User, required_roles: List[UserRole]) -> bool:
    """
    Check if user has one of the required roles (considering hierarchy)
    """
    if not user or not user.role:
        return False
    
    user_role = user.role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            return False
    
    # Check if user has any of the required roles
    for required_role in required_roles:
        if user_role in ROLE_HIERARCHY.get(required_role, []):
            return True
    
    return False


def check_permission(user: User, resource: str, action: str) -> bool:
    """
    Check if user has permission to perform action on resource
    """
    if not user or not user.role:
        return False
    
    user_role = user.role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            return False
    
    permissions = ROLE_PERMISSIONS.get(user_role, {})
    resource_permissions = permissions.get(resource, [])
    
    return action in resource_permissions


def require_roles(allowed_roles: List[UserRole]):
    """
    Decorator to require specific roles for endpoint access
    Usage:
        @require_roles([UserRole.ADMIN, UserRole.CISO])
        async def some_endpoint(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user') or kwargs.get('user')
            
            if not current_user:
                # Try to find in args
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not check_role(current_user, allowed_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(resource: str, action: str):
    """
    Decorator to require specific permission for endpoint access
    Usage:
        @require_permission("vulnerabilities", "create")
        async def create_vulnerability(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user') or kwargs.get('user')
            
            if not current_user:
                # Try to find in args
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not check_permission(current_user, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {action} on {resource}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Helper dependency for FastAPI endpoints
def RoleChecker(allowed_roles: List[UserRole]):
    """
    FastAPI dependency to check user roles
    Usage:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
        async def admin_endpoint():
            ...
    """
    def check_roles(current_user: User):
        if not check_role(current_user, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return check_roles


def PermissionChecker(resource: str, action: str):
    """
    FastAPI dependency to check user permissions
    Usage:
        @router.post("/vulnerabilities", dependencies=[Depends(PermissionChecker("vulnerabilities", "create"))])
        async def create_vuln():
            ...
    """
    def check_perms(current_user: User):
        if not check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {action} on {resource}"
            )
        return current_user
    return check_perms
