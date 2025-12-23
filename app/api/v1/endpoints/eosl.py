"""EOSL (End of Service Life) API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from app.db.session import get_session
from app.services.eosl_service import eosl_service
from app.schemas.eosl import (
    EOSLAssetCreate, EOSLAssetUpdate, EOSLAssetResponse,
    EOSLAssetListResponse, EOSLDashboardResponse,
    AssetUploadRequest, AssetUploadResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=EOSLDashboardResponse)
async def get_eosl_dashboard(
    year: Optional[int] = Query(None, description="Year for compliance data"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get complete EOSL dashboard data including:
    - All EOSL assets
    - Top non-compliant assets by type
    - Compliance trends by year
    - Summary statistics (EOS/EOL counts, expiring soon, expired)
    """
    try:
        dashboard_data = await eosl_service.get_dashboard_data(db, year)
        return dashboard_data
    except Exception as e:
        logger.error(f"Error fetching EOSL dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch EOSL dashboard data: {str(e)}"
        )


@router.get("/", response_model=EOSLAssetListResponse)
async def get_eosl_assets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    eosl_type: Optional[str] = Query(None, description="Filter by EOSL type (EOS/EOL)"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    db: AsyncSession = Depends(get_session)
):
    """Get paginated list of EOSL assets with optional filters"""
    try:
        assets = await eosl_service.get_assets(db, skip, limit, eosl_type, owner)
        return assets
    except Exception as e:
        logger.error(f"Error fetching EOSL assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch EOSL assets: {str(e)}"
        )


@router.get("/{asset_id}", response_model=EOSLAssetResponse)
async def get_eosl_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Get single EOSL asset by ID"""
    try:
        asset = await eosl_service.get_asset_by_id(db, asset_id)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EOSL asset with id {asset_id} not found"
            )
        
        return asset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching EOSL asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch EOSL asset: {str(e)}"
        )


@router.post("/", response_model=EOSLAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_eosl_asset(
    asset_data: EOSLAssetCreate,
    db: AsyncSession = Depends(get_session)
):
    """Create new EOSL asset"""
    try:
        asset = await eosl_service.create_asset(db, asset_data)
        return asset
    except Exception as e:
        logger.error(f"Error creating EOSL asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create EOSL asset: {str(e)}"
        )


@router.put("/{asset_id}", response_model=EOSLAssetResponse)
async def update_eosl_asset(
    asset_id: int,
    asset_data: EOSLAssetUpdate,
    db: AsyncSession = Depends(get_session)
):
    """Update EOSL asset"""
    try:
        asset = await eosl_service.update_asset(db, asset_id, asset_data)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EOSL asset with id {asset_id} not found"
            )
        
        return asset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating EOSL asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update EOSL asset: {str(e)}"
        )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_eosl_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Delete EOSL asset"""
    try:
        deleted = await eosl_service.delete_asset(db, asset_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EOSL asset with id {asset_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting EOSL asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete EOSL asset: {str(e)}"
        )


@router.post("/upload", response_model=AssetUploadResponse)
async def bulk_upload_assets(
    upload_data: AssetUploadRequest,
    db: AsyncSession = Depends(get_session)
):
    """Bulk upload EOSL assets"""
    try:
        result = await eosl_service.bulk_create_assets(db, upload_data.assets)
        
        return AssetUploadResponse(
            success=result["success"],
            created=result["created"],
            failed=result["failed"],
            errors=result.get("errors")
        )
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload assets: {str(e)}"
        )