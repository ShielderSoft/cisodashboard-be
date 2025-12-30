from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.crud.crud_user import user_crud
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api.v1.endpoints.auth import admin_required
from fastapi import Body

router = APIRouter()


@router.get("/")
async def get_users(
    db: AsyncSession = Depends(get_session)
):
    """Get list of users"""
    users = await db.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = users.fetchall()
    # convert to simple list of dicts
    result = []
    for r in rows:
        result.append({k: getattr(r, k) if hasattr(r, k) else None for k in r.keys()})
    return {"items": result}


@router.post("/")
async def create_user(
    db: AsyncSession = Depends(get_session),
    payload: UserCreate = Body(...)
):
    """Create new user"""
    try:
        user = await user_crud.create(db, obj_in=payload)
        # convert SQLAlchemy model to dict for JSON serialization and remove sensitive fields
        user_dict = {k: getattr(user, k) if hasattr(user, k) else None for k in user.__dict__.keys() if not k.startswith('_')}
        user_dict.pop('hashed_password', None)
        return UserResponse(**user_dict)
    except ValueError as ve:
        # client error (e.g., password too long)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # unexpected server error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Get user by ID"""
    q = await db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
    row = q.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {k: getattr(row, k) if hasattr(row, k) else None for k in row.keys()}


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Update user"""
    # Expect full or partial update via JSON body
    body = await db._run_soon(None)
    # Fallback: use user_crud update after fetching user
    q = await db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
    row = q.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    # Minimal: return existing row (detailed update handled by user_crud.update when wired)
    return {k: getattr(row, k) if hasattr(row, k) else None for k in row.keys()}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Delete user"""
    await db.execute("DELETE FROM users WHERE id = :id", {"id": user_id})
    await db.commit()
    return {"message": "User deleted"}