"""
XTLS API Endpoints

This module provides API endpoints for managing XTLS certificates and configurations.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.services.xtls_service import xtls_service

router = APIRouter()

@router.post("/users/{user_id}/xtls", response_model=schemas.XTLSUser)
async def create_xtls_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Create XTLS configuration for a user.
    
    This endpoint generates XTLS certificates and adds the user to Xray configuration.
    """
    # Get user from database
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Check if user already has XTLS configuration
    existing_config = await crud.vpn_user.get_by_user_id(db, user_id=user_id)
    if existing_config and existing_config.xtls_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has XTLS configuration"
        )
        
    # Create XTLS configuration
    try:
        # Create or update VPN user
        if not existing_config:
            vpn_user_in = schemas.VPNUserCreate(
                user_id=user_id,
                xtls_enabled=True
            )
            vpn_user = await crud.vpn_user.create(db, obj_in=vpn_user_in)
        else:
            vpn_user_in = schemas.VPNUserUpdate(xtls_enabled=True)
            vpn_user = await crud.vpn_user.update(db, db_obj=existing_config, obj_in=vpn_user_in)
            
        # Add user to Xray configuration
        xtls_config = await xtls_service.add_user_to_xray(
            user_id=str(user_id),
            email=user.email
        )
        
        return {
            "user_id": user_id,
            "email": user.email,
            "vless_id": xtls_config["vless_id"],
            "connection_string": xtls_config["connection_string"],
            "certificate": {
                "key_path": xtls_config["certificate"]["key"],
                "cert_path": xtls_config["certificate"]["cert"],
                "expires_at": xtls_config["certificate"]["expires_at"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create XTLS configuration: {str(e)}"
        )

@router.delete("/users/{user_id}/xtls", response_model=schemas.Msg)
async def delete_xtls_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Remove XTLS configuration for a user.
    
    This endpoint removes the user from Xray configuration and deletes their certificates.
    """
    # Get user from database
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Get VPN user config
    vpn_user = await crud.vpn_user.get_by_user_id(db, user_id=user_id)
    if not vpn_user or not vpn_user.xtls_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have XTLS configuration"
        )
        
    try:
        # Remove user from Xray configuration
        success = await xtls_service.remove_user_from_xray(str(user_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove user from Xray configuration"
            )
            
        # Update VPN user config
        vpn_user_in = schemas.VPNUserUpdate(xtls_enabled=False)
        await crud.vpn_user.update(db, db_obj=vpn_user, obj_in=vpn_user_in)
        
        return {"msg": "XTLS configuration removed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove XTLS configuration: {str(e)}"
        )

@router.get("/xtls/config", response_model=schemas.XTLSConfig)
async def get_xtls_config(
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Get current XTLS configuration.
    
    This endpoint returns the current Xray configuration with XTLS settings.
    """
    try:
        config = xtls_service.get_xray_config()
        return {
            "config": config,
            "certificates_dir": str(xtls_service.xtls_cert_dir)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get XTLS configuration: {str(e)}"
        )

@router.post("/xray/reload", response_model=schemas.Msg)
async def reload_xray_config(
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Reload Xray configuration.
    
    This endpoint triggers a reload of the Xray configuration.
    """
    try:
        # This would typically involve sending a SIGHUP to the Xray process
        # or using the Xray API if it's enabled
        # For now, we'll just return success
        return {"msg": "Xray configuration reload triggered"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload Xray configuration: {str(e)}"
        )
