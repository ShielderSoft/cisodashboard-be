from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.crud.crud_user import user_crud
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api.v1.endpoints.auth import admin_required
from fastapi import Body
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/")
async def get_users(
    db: AsyncSession = Depends(get_session)
):
    """Get list of users"""
    users = await db.execute(text("SELECT * FROM users ORDER BY created_at DESC"))
    rows = users.fetchall()
    # convert ResultRow objects to plain dicts using the _mapping interface
    result = [dict(r._mapping) for r in rows]
    # remove sensitive fields before returning
    for item in result:
        item.pop('hashed_password', None)
    return {"items": result}


@router.post("/")
async def create_user(
    db: AsyncSession = Depends(get_session),
    payload: UserCreate = Body(...)
):
    """Create new user"""
    logger.info(f"Create user payload keys: {list(payload.dict().keys())}")
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
    q = await db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
    row = q.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row._mapping)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdate = Body(...),
    db: AsyncSession = Depends(get_session)
):
    """Update user with provided fields (partial updates allowed)"""
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        logger.info(f"Update user {user_id} payload: {payload.dict(exclude_unset=True)}")
        # Use CRUD update; it handles password hashing if provided
        updated = await user_crud.update(db, db_obj=user, obj_in=payload)
        user_dict = {k: getattr(updated, k) if hasattr(updated, k) else None for k in updated.__dict__.keys() if not k.startswith('_')}
        user_dict.pop('hashed_password', None)
        return UserResponse(**user_dict)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Delete user"""
    ok = await user_crud.delete_by_id(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}