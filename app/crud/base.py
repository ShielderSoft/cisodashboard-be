from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        try:
            query = select(self.model).where(self.model.id == id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error in get: {str(e)}")
            raise

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination"""
        try:
            query = select(self.model).offset(skip).limit(limit)
            result = await db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error in get_multi: {str(e)}")
            raise

    async def create(self, db: AsyncSession, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """Create a new record"""
        try:
            if isinstance(obj_in, dict):
                obj_in_data = obj_in
            else:
                obj_in_data = obj_in.model_dump(exclude_unset=True)
            
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Error in create: {str(e)}")
            await db.rollback()
            raise

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record"""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Error in update: {str(e)}")
            await db.rollback()
            raise

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType:
        """Delete a record by ID"""
        try:
            obj = await self.get(db, id)
            if obj:
                await db.delete(obj)
                await db.commit()
            return obj
        except Exception as e:
            logger.error(f"Error in remove: {str(e)}")
            await db.rollback()
            raise

    async def count(self, db: AsyncSession) -> int:
        """Get total count of records"""
        try:
            query = select(func.count(self.model.id))
            result = await db.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Error in count: {str(e)}")
            raise

    async def exists(self, db: AsyncSession, *, id: Any) -> bool:
        """Check if a record exists by ID"""
        try:
            query = select(self.model.id).where(self.model.id == id)
            result = await db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error in exists: {str(e)}")
            raise