from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import security_manager
from app.crud.crud_user import user_crud
from app.schemas.user import UserCreate
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def init_db(session: AsyncSession) -> None:
    """Initialize database with default data"""
    
    logger.info("🔧 Initializing database...")
    
    # Create superuser if it doesn't exist
    superuser = await user_crud.get_by_email(session, email="admin@risktrix.com")
    
    if not superuser:
        logger.info("Creating superuser...")
        superuser_in = UserCreate(
            email="admin@risktrix.com",
            username="admin",
            full_name="RiskTrix Administrator",
            password="admin123",  # Change this in production!
            is_active=True,
            is_superuser=True,
            role="admin"
        )
        superuser = await user_crud.create(session, obj_in=superuser_in)
        logger.info(f"✅ Superuser created: {superuser.email}")
    else:
        logger.info("Superuser already exists")
    
    # Add other initialization logic here
    logger.info("✅ Database initialization completed")