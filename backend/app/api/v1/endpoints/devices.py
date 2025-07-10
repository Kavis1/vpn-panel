"""
API endpoints для управления устройствами пользователей.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.services.device_service import DeviceService

router = APIRouter()

@router.get("/", response_model=schemas.DeviceList)
async def read_devices(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить список устройств текущего пользователя с информацией о лимитах.
    
    Параметры:
    - skip: Количество пропускаемых записей
    - limit: Максимальное количество возвращаемых записей
    - include_inactive: Включать ли неактивные устройства
    
    Возвращает:
    - Список устройств с информацией о лимитах
    """
    device_service = DeviceService(db)
    try:
        devices, total, limit_info = await device_service.get_user_devices(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
        
        # Вычисляем общее количество страниц
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return {
            "items": devices,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "size": limit,
            "pages": pages,
            "limits": limit_info
        }
    except Exception as e:
        logger.error(f"Ошибка при получении списка устройств: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список устройств"
        )

@router.post("/register", response_model=schemas.Device)
async def register_device(
    request: Request,
    device_in: schemas.DeviceCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Зарегистрировать новое устройство с проверкой лимита устройств.
    
    Если включена проверка лимита устройств (HWID_DEVICE_LIMIT_ENABLED=True),
    то будет проверяться, не превышает ли количество устройств пользователя
    установленный лимит.
    
    Параметры:
    - device_in: Данные устройства для регистрации
    
    Возвращает:
    - Зарегистрированное устройство
    
    Возможные ошибки:
    - 403: Превышен лимит устройств
    - 500: Ошибка при регистрации устройства
    """
    device_service = DeviceService(db)
    
    try:
        # Получаем IP-адрес клиента
        ip_address = None
        if request.client:
            ip_address = request.client.host
        
        # Регистрируем устройство с проверкой лимита
        device = await device_service.register_device(
            device_in=device_in,
            user=current_user,
            ip_address=ip_address,
            request=request  # Передаем запрос для проверки лимита
        )
        
        return device
        
    except HTTPException:
        # Пробрасываем HTTP-исключения как есть
        raise
    except Exception as e:
        logger.error(f"Ошибка при регистрации устройства: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось зарегистрировать устройство"
        )

@router.get("/{device_id}", response_model=schemas.Device)
async def read_device(
    device_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить информацию об устройстве по ID.
    """
    device_service = DeviceService(db)
    device = await device_service.get_device(
        device_id=device_id,
        user=current_user
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )
    
    return device

@router.put("/{device_id}", response_model=schemas.Device)
async def update_device(
    device_id: int,
    device_in: schemas.DeviceUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Обновить информацию об устройстве.
    """
    device_service = DeviceService(db)
    device = await device_service.update_device(
        device_id=device_id,
        device_in=device_in,
        user=current_user
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )
    
    return device

@router.delete("/{device_id}", response_model=schemas.Device)
async def delete_device(
    device_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Удалить устройство.
    """
    device_service = DeviceService(db)
    device = await device_service.delete_device(
        device_id=device_id,
        user=current_user
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )
    
    return device

@router.post("/{device_id}/revoke", response_model=schemas.Device)
async def revoke_device(
    device_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Отозвать устройство (деактивировать).
    """
    device_service = DeviceService(db)
    device = await device_service.revoke_device(
        device_id=device_id,
        user=current_user
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено или недостаточно прав"
        )
    
    return device

@router.post("/{device_id}/trust", response_model=schemas.Device)
async def trust_device(
    device_id: int,
    trusted: bool = True,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Пометить устройство как доверенное или наоборот.
    """
    device_service = DeviceService(db)
    device = await device_service.trust_device(
        device_id=device_id,
        trusted=trusted,
        user=current_user
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено или недостаточно прав"
        )
    
    return device

@router.get("/check-limit", response_model=Dict[str, Any])
async def check_device_limit(
    request: Request,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Проверить лимит устройств для текущего пользователя.
    
    Возвращает информацию о текущем лимите устройств и количестве
    уже зарегистрированных устройств.
    
    Возвращает:
    - limit_enabled: Включена ли проверка лимита устройств
    - device_limit: Максимальное разрешенное количество устройств
    - current_devices: Текущее количество активных устройств
    - can_add_more: Можно ли зарегистрировать еще устройства
    - message: Сообщение о лимите (если достигнут лимит)
    """
    device_service = DeviceService(db)
    
    try:
        # Получаем информацию о лимитах
        _, _, limit_info = await device_service.get_user_devices(
            user_id=current_user.id,
            skip=0,
            limit=1,
            include_inactive=False
        )
        
        return limit_info
        
    except Exception as e:
        logger.error(f"Ошибка при проверке лимита устройств: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось проверить лимит устройств"
        )

@router.get("/stats/summary", response_model=schemas.DeviceStats)
async def get_devices_stats(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить сводную статистику по устройствам.
    """
    device_service = DeviceService(db)
    
    # Если пользователь не администратор, возвращаем статистику только по его устройствам
    user_id = current_user.id if not current_user.is_superuser else None
    
    return await device_service.get_device_stats(user_id=user_id)
