from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.get("/")
async def get_users(
    db: AsyncSession = Depends(get_session)
):
    """Get list of users"""
    return {"message": "Users endpoint - to be implemented"}


@router.post("/")
async def create_user(
    db: AsyncSession = Depends(get_session)
):
    """Create new user"""
    return {"message": "Create user endpoint - to be implemented"}


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Get user by ID"""
    return {"message": f"Get user {user_id} - to be implemented"}


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Update user"""
    return {"message": f"Update user {user_id} - to be implemented"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Delete user"""
    return {"message": f"Delete user {user_id} - to be implemented"}