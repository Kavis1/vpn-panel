"""
API endpoints for managing VPN nodes.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.services.node import NodeService
from app.models.node import NodeStatus

router = APIRouter()

@router.get("/", response_model=List[schemas.Node])
async def read_nodes(
    skip: int = 0,
    limit: int = 100,
    status: Optional[NodeStatus] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Retrieve nodes with optional filtering by status.
    """
    filter_params = {}
    if status is not None:
        filter_params["status"] = status
    
    nodes = await crud.node.get_multi(
        db, 
        filter_params=filter_params,
        skip=skip, 
        limit=limit
    )
    return nodes

@router.post("/", response_model=schemas.Node)
async def create_node(
    node_in: schemas.NodeCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Create a new node.
    """
    node_service = NodeService(db)
    
    try:
        node = await node_service.register_node(node_in)
        return node
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create node: {str(e)}"
        )

@router.get("/{node_id}", response_model=schemas.Node)
async def read_node(
    node_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Get a specific node by ID.
    """
    node = await crud.node.get(db, id=node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    return node

@router.put("/{node_id}", response_model=schemas.Node)
async def update_node(
    node_id: int,
    node_in: schemas.NodeUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Update a node.
    """
    node = await crud.node.get(db, id=node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    node = await crud.node.update(db, db_obj=node, obj_in=node_in)
    return node

@router.delete("/{node_id}", response_model=schemas.Node)
async def delete_node(
    node_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Delete a node.
    """
    node = await crud.node.get(db, id=node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    node = await crud.node.remove(db, id=node_id)
    return node

@router.post("/{node_id}/sync", response_model=Dict[str, Any])
async def sync_node(
    node_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Sync configuration with a node.
    """
    node_service = NodeService(db)
    
    try:
        success = await node_service.sync_node_config(node_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync node configuration"
            )
            
        return {"status": "success", "message": "Node configuration synced successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to sync node: {str(e)}"
        )

@router.get("/{node_id}/stats", response_model=Dict[str, Any])
async def get_node_stats(
    node_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Get statistics for a specific node.
    """
    node_service = NodeService(db)
    
    try:
        stats = await node_service.get_node_stats(node_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node stats: {str(e)}"
        )

@router.post("/{node_id}/status", response_model=Dict[str, Any])
async def update_node_status(
    node_id: int,
    status_update: Dict[str, Any],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Update node status.
    """
    node_service = NodeService(db)
    
    try:
        node = await node_service.update_node_status(
            node_id=node_id,
            status=status_update.get("status"),
            status_message=status_update.get("status_message", "")
        )
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
            
        return {"status": "success", "message": "Node status updated successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update node status: {str(e)}"
        )

@router.get("/health/check", response_model=Dict[str, Any])
async def check_nodes_health(
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Check health of all nodes.
    """
    node_service = NodeService(db)
    
    try:
        results = await node_service.check_nodes_health()
        return {
            "status": "success",
            "results": results,
            "total": len(results),
            "online": sum(1 for status in results.values() if status),
            "offline": sum(1 for status in results.values() if not status)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check nodes health: {str(e)}"
        )

@router.post("/register", response_model=Dict[str, Any])
async def register_node(
    node_in: schemas.NodeCreate,
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Register a new node (for node self-registration).
    """
    node_service = NodeService(db)
    
    try:
        node = await node_service.register_node(node_in)
        return {
            "status": "success",
            "node_id": node.id,
            "auth_token": node.auth_token,
            "message": "Node registered successfully"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register node: {str(e)}"
        )

@router.post("/authenticate", response_model=Dict[str, Any])
async def authenticate_node(
    credentials: Dict[str, str],
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Authenticate a node (for node authentication).
    """
    node_service = NodeService(db)
    
    try:
        fqdn = credentials.get("fqdn")
        token = credentials.get("token")
        
        if not fqdn or not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FQDN and token are required"
            )
        
        node = await node_service.authenticate_node(fqdn, token)
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
        return {
            "status": "success",
            "node_id": node.id,
            "message": "Node authenticated successfully"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )
