"""
API endpoints for Xray configuration and management.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.services.xray import XrayService

router = APIRouter()

@router.get("/config", response_model=Dict[str, Any])
async def get_xray_config(
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Get current Xray configuration.
    """
    xray_service = XrayService()
    config = await xray_service._load_config()
    return config.dict()

@router.post("/config", response_model=Dict[str, Any])
async def update_xray_config(
    config_in: Dict[str, Any],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Update Xray configuration.
    """
    xray_service = XrayService()
    
    try:
        # Validate the configuration
        validated_config = xray_service._validate_config(config_in)
        
        # Save the configuration
        await xray_service._save_config(validated_config.dict())
        
        # Reload Xray to apply changes
        success = await xray_service._reload_config()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload Xray configuration"
            )
            
        return {"status": "success", "message": "Configuration updated successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/users", response_model=List[Dict[str, Any]])
async def get_xray_users(
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Get all users from Xray configuration.
    """
    xray_service = XrayService()
    config = await xray_service._load_config()
    
    users = []
    for inbound in config.inbounds:
        if 'settings' in inbound and 'clients' in inbound['settings']:
            for client in inbound['settings']['clients']:
                users.append({
                    "id": client.get('id'),
                    "email": client.get('email'),
                    "protocol": inbound.get('protocol'),
                    "port": inbound.get('port')
                })
    
    return users

@router.post("/users/{user_id}", response_model=Dict[str, Any])
async def add_xray_user(
    user_id: str,
    user_in: Dict[str, Any],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Add a user to Xray configuration.
    """
    xray_service = XrayService()
    
    try:
        # Create a temporary user object
        user = schemas.UserCreate(
            email=user_in.get('email', ''),
            password="",  # Not used for Xray
            full_name=user_in.get('full_name', '')
        )
        
        # Add user to Xray
        success = await xray_service.add_user(user, protocol=user_in.get('protocol', 'vless'))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add user to Xray"
            )
            
        return {"status": "success", "message": "User added successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def remove_xray_user(
    user_id: str,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Remove a user from Xray configuration.
    """
    xray_service = XrayService()
    
    try:
        # Remove user from Xray
        success = await xray_service.remove_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Xray configuration"
            )
            
        return {"status": "success", "message": "User removed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_xray_stats(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Get Xray statistics.
    """
    xray_service = XrayService()
    
    try:
        stats = await xray_service.get_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Xray stats: {str(e)}"
        )

@router.post("/restart", response_model=Dict[str, Any])
async def restart_xray(
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Restart Xray service.
    """
    xray_service = XrayService()
    
    try:
        success = await xray_service.restart()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restart Xray"
            )
            
        return {"status": "success", "message": "Xray restarted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart Xray: {str(e)}"
        )
