from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_session
from app.crud.crud_user import user_crud
from app.core.security import security_manager, security
from app.schemas.user import UserResponse

router = APIRouter()


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict  # User profile information


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session),
):
    """Dependency to get current user from access token"""
    token = security_manager.extract_token_from_credentials(credentials)
    payload = security_manager.verify_token(token)

    # Expect token type to be 'access'
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await user_crud.get_by_email(db, payload.get("email"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def admin_required(user=Depends(get_current_user)):
    """Dependency that ensures the current user has admin privileges."""
    try:
        role_val = user.role.value if hasattr(user.role, 'value') else user.role
    except Exception:
        role_val = getattr(user, 'role', None)

    if not role_val or str(role_val).lower() != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin privileges required')

    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_session)):
    """Authenticate user with email/username and password, return access + refresh tokens"""
    # Validate that at least email or username is provided
    if not payload.email and not payload.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Either email or username must be provided"
        )
    
    # Try to authenticate with email first, then username
    user = None
    if payload.email:
        user = await user_crud.authenticate(db, payload.email, payload.password)
    
    if not user and payload.username:
        # Get user by username first, then verify password
        user_by_username = await user_crud.get_by_username(db, payload.username)
        if user_by_username and security_manager.verify_password(payload.password, user_by_username.hashed_password):
            user = user_by_username
            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            await db.commit()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Prepare token payload - include minimal role info
    role_val = user.role.value if hasattr(user.role, "value") else user.role
    token_data = {"sub": str(user.id), "email": user.email, "roles": [role_val]}

    access_token = security_manager.create_access_token(token_data)
    refresh_token = security_manager.create_refresh_token(token_data)

    # Prepare user profile information to return with tokens
    user_profile = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": role_val,
        "profile_type": getattr(user, 'profile_type', None),
        "privilege_level": getattr(user, 'privilege_level', None),
        "clearance_level": getattr(user, 'clearance_level', None),
        "company": getattr(user, 'company', None),
        "phone": getattr(user, 'phone', None),
        "department": getattr(user, 'department', None),
        "is_active": user.is_active,
    }

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "user": user_profile
    }


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_session)):
    """Exchange a valid refresh token for a new access token"""
    try:
        payload = security_manager.verify_token(body.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    # Ensure user still exists
    user = await user_crud.get_by_email(db, payload.get("email"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    role_val = user.role.value if hasattr(user.role, "value") else user.role
    new_access = security_manager.create_access_token({"sub": str(user.id), "email": user.email, "roles": [role_val]})

    new_refresh = security_manager.create_refresh_token({"sub": str(user.id), "email": user.email, "roles": [role_val]})

    return {"access_token": new_access, "refresh_token": new_refresh}


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout endpoint. For now this is a client-side operation (token removal).
    If you want server-side revocation, implement a blacklist/redis store keyed by jti."""
    token = security_manager.extract_token_from_credentials(credentials)
    # No server-side revocation implemented yet
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    """Return current authenticated user's profile"""
    return user