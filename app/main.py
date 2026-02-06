from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import SessionLocal, sync_engine
from app.utils.logger import setup_logger
from sqlalchemy import text
from app.core.config import settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.vendor_expiry_notification import vendor_expiry_notification_service
from app.db.session import SessionLocal as AsyncSessionLocal

logger = setup_logger(__name__)

# Scheduler for periodic tasks (vendor expiry notifications)
scheduler = AsyncIOScheduler()

async def _scheduled_expiry_check():
    """Run vendor expiry notification check for vendors expiring in 8 days."""
    # Use an async session factory to run the check
    async with AsyncSessionLocal() as db:
        try:
            await vendor_expiry_notification_service.check_and_notify_expiring_vendors(db=db, days_before=8)
        except Exception as e:
            logger.error(f"Error running scheduled expiry check: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting RiskTrix Backend Application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.API_VERSION}")
    
    # Start scheduler
    try:
        scheduler.add_job(_scheduled_expiry_check, 'cron', hour=9, minute=0, id='daily_vendor_expiry_check')
        scheduler.start()
        logger.info("✅ Scheduler started: daily vendor expiry check at 09:00 AM")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
    
    yield
    
    # Shutdown scheduler
    try:
        scheduler.shutdown(wait=False)
        logger.info("✅ Scheduler shut down")
    except Exception:
        pass
    
    logger.info("🛑 Shutting down RiskTrix Backend Application...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Enterprise CISO Dashboard - Cybersecurity Risk Management Platform",
        version=settings.API_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page-Count"]
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"📨 {request.method} {request.url}")
        
        response = await call_next(request)
        
        # Log response time
        process_time = time.time() - start_time
        logger.info(f"⚡ Completed in {process_time:.4f}s - Status: {response.status_code}")
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"🚨 Global exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error",
                "detail": "An unexpected error occurred" if settings.ENVIRONMENT == "production" else str(exc)
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT
        }
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,
        log_level="info"
    )