from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.post("/login")
async def login(
    db: AsyncSession = Depends(get_session)
):
    """User login endpoint"""
    return {"message": "Login endpoint - to be implemented"}


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_session)
):
    """User logout endpoint"""
    return {"message": "Logout endpoint - to be implemented"}


@router.post("/refresh")
async def refresh_token(
    db: AsyncSession = Depends(get_session)
):
    """Refresh token endpoint"""
    return {"message": "Token refresh endpoint - to be implemented"}