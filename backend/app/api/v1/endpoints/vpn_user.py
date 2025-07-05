"""
API endpoints для управления пользователями VPN.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.models.vpn_user import VPNUserStatus
from app.services.vpn_user import VPNUserService

router = APIRouter()

@router.get("/", response_model=List[schemas.VPNUser])
async def read_vpn_users(
    skip: int = 0,
    limit: int = 100,
    status: Optional[VPNUserStatus] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить список пользователей VPN с возможностью фильтрации по статусу.
    """
    # Проверяем права доступа
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра списка пользователей"
        )
    
    # Формируем параметры фильтрации
    filter_params = {}
    if status is not None:
        filter_params["status"] = status
    
    # Получаем список пользователей
    users = await crud.vpn_user.get_multi(
        db,
        skip=skip,
        limit=limit,
        filter_params=filter_params
    )
    
    return users

@router.post("/", response_model=schemas.VPNUser)
async def create_vpn_user(
    user_in: schemas.VPNUserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Создать нового пользователя VPN.
    """
    vpn_user_service = VPNUserService(db)
    return await vpn_user_service.create_user(user_in, current_user)

@router.get("/me", response_model=schemas.VPNUser)
async def read_vpn_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить информацию о текущем пользователе VPN.
    """
    vpn_user_service = VPNUserService(db)
    user_stats = await vpn_user_service.get_user_stats(current_user.id)
    return user_stats

@router.get("/{user_id}", response_model=schemas.VPNUser)
async def read_vpn_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить информацию о пользователе VPN по ID.
    """
    # Проверяем права доступа
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этого пользователя"
        )
    
    vpn_user_service = VPNUserService(db)
    user_stats = await vpn_user_service.get_user_stats(user_id)
    return user_stats

@router.put("/{user_id}", response_model=schemas.VPNUser)
async def update_vpn_user(
    user_id: int,
    user_in: schemas.VPNUserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Обновить данные пользователя VPN.
    """
    # Проверяем права доступа
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления этого пользователя"
        )
    
    vpn_user_service = VPNUserService(db)
    return await vpn_user_service.update_user(user_id, user_in, current_user)

@router.delete("/{user_id}", response_model=schemas.VPNUser)
async def delete_vpn_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Удалить пользователя VPN.
    """
    vpn_user_service = VPNUserService(db)
    return await vpn_user_service.delete_user(user_id, current_user)

@router.post("/{user_id}/status", response_model=schemas.VPNUser)
async def update_vpn_user_status(
    user_id: int,
    status_update: Dict[str, str],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Обновить статус пользователя VPN.
    """
    vpn_user_service = VPNUserService(db)
    
    try:
        status = VPNUserStatus(status_update["status"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Допустимые значения: {', '.join([s.value for s in VPNUserStatus])}"
        )
    
    return await vpn_user_service.update_status(user_id, status, current_user)

@router.post("/{user_id}/reset-traffic", response_model=schemas.VPNUser)
async def reset_vpn_user_traffic(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Сбросить статистику использования трафика пользователя.
    """
    vpn_user_service = VPNUserService(db)
    return await vpn_user_service.reset_traffic(user_id, current_user)

@router.get("/{user_id}/stats", response_model=Dict[str, Any])
async def get_vpn_user_stats(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить статистику использования трафика пользователя.
    """
    # Проверяем права доступа
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра статистики этого пользователя"
        )
    
    vpn_user_service = VPNUserService(db)
    return await vpn_user_service.get_user_stats(user_id)

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_vpn_users_summary(
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить сводную статистику по пользователям VPN.
    """
    # Общее количество пользователей
    total_users = await crud.vpn_user.count(db)
    
    # Количество пользователей по статусам
    active_users = await crud.vpn_user.count_by_status(db, VPNUserStatus.ACTIVE)
    suspended_users = await crud.vpn_user.count_by_status(db, VPNUserStatus.SUSPENDED)
    expired_users = await crud.vpn_user.count_by_status(db, VPNUserStatus.EXPIRED)
    
    # Общий использованный трафик
    traffic_stats = await crud.vpn_user.get_traffic_stats(db)
    
    # Последние активные пользователи
    recent_users = await crud.vpn_user.get_recently_active(db, limit=5)
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "suspended_users": suspended_users,
        "expired_users": expired_users,
        "traffic_stats": {
            "total_upload": traffic_stats["total_upload"],
            "total_download": traffic_stats["total_download"],
            "total_traffic": traffic_stats["total_upload"] + traffic_stats["total_download"]
        },
        "recent_users": [
            {
                "id": user.id,
                "username": user.username,
                "last_active_at": user.last_active_at,
                "status": user.status
            }
            for user in recent_users
        ]
    }
