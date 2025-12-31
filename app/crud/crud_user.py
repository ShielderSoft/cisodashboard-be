from typing import Any, Dict, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.models.models import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import security_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class UserCRUD:
    """CRUD operations for users"""

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            return None

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            return None

    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by id {user_id}: {str(e)}")
            return None

    async def delete_by_id(self, db: AsyncSession, user_id: int) -> bool:
        """Delete user by ID"""
        try:
            user = await self.get_by_id(db, user_id)
            if not user:
                return False
            await db.delete(user)
            await db.commit()
            logger.info(f"Deleted user id {user_id}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create a new user"""
        try:
            # Validate password length (bcrypt has a 72-byte input limit)
            if not obj_in.password:
                raise ValueError("Password is required")
            pw_bytes = obj_in.password.encode("utf-8")
            # Log only the byte length for debugging (do NOT log the raw password)
            logger.info(f"Password byte length: {len(pw_bytes)} for user {obj_in.email}")
            if len(pw_bytes) > 72:
                raise ValueError("Password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])")

            # Hash password
            hashed_password = security_manager.get_password_hash(obj_in.password)
            
            # Create user data dict
            user_data = obj_in.dict(exclude={'password'})
            user_data['hashed_password'] = hashed_password
            
            # Create user instance
            db_user = User(**user_data)
            
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            
            logger.info(f"Created user: {db_user.email} (ID: {db_user.id})")
            return db_user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise

    async def update(self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
        """Update user"""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            
            # Handle password update
            if 'password' in update_data:
                hashed_password = security_manager.get_password_hash(update_data['password'])
                update_data['hashed_password'] = hashed_password
                del update_data['password']
            
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            await db.commit()
            await db.refresh(db_obj)
            
            logger.info(f"Updated user: {db_obj.email} (ID: {db_obj.id})")
            return db_obj
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user {db_obj.id}: {str(e)}")
            raise

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_by_email(db, email)
            if not user:
                return None
            
            if not security_manager.verify_password(password, user.hashed_password):
                return None
            
            # Update last login
            await self.update(db, db_obj=user, obj_in={'last_login': datetime.utcnow()})
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {str(e)}")
            return None


# Create instance
user_crud = UserCRUD()