import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.device import Device
from app.models.user import User
from app.crud.crud_device import crud_device

logger = logging.getLogger(__name__)

class DeviceLimitService:
    """
    Сервис для управления лимитами устройств пользователей.
    Вдохновлено функционалом HWID-лимитов из Remnawave.
    """
    
    def __init__(self):
        self.enabled = getattr(settings, "HWID_DEVICE_LIMIT_ENABLED", False)
        self.fallback_limit = getattr(settings, "HWID_FALLBACK_DEVICE_LIMIT", 5)
        self.max_devices_message = getattr(
            settings, 
            "HWID_MAX_DEVICES_ANNOUNCE", 
            "You have reached the maximum number of allowed devices for your subscription."
        )
    
    def generate_device_id(self, request: Request, user_agent: str) -> str:
        """
        Генерация уникального идентификатора устройства на основе запроса.
        
        Args:
            request: FastAPI Request объект
            user_agent: User-Agent строка
            
        Returns:
            str: Уникальный идентификатор устройства (хеш)
        """
        # Собираем информацию об устройстве
        ip = request.client.host if request.client else "unknown"
        accept_language = request.headers.get("accept-language", "")
        
        # Создаем строку для хеширования
        device_info = f"{ip}:{user_agent}:{accept_language}"
        
        # Генерируем хеш
        return hashlib.sha256(device_info.encode()).hexdigest()
    
    async def check_device_limit(
        self, 
        db: AsyncSession, 
        user: User,
        device_id: str,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Проверяет, не превышен ли лимит устройств для пользователя.
        
        Args:
            db: Асинхронная сессия БД
            user: Пользователь
            device_id: Идентификатор устройства
            request: FastAPI Request объект (опционально)
            
        Returns:
            Dict[str, Any]: Информация о результате проверки
            
        Raises:
            HTTPException: Если лимит устройств превышен
        """
        if not self.enabled:
            return {"allowed": True, "message": "Device limit check is disabled"}
        
        # Получаем лимит устройств для пользователя (или используем значение по умолчанию)
        device_limit = getattr(user, "device_limit", self.fallback_limit)
        
        # Если лимит не установлен или равен 0, пропускаем проверку
        if not device_limit or device_limit <= 0:
            return {"allowed": True, "message": "No device limit set for user"}
        
        # Получаем все активные устройства пользователя
        devices = await crud_device.get_multi_by_owner(
            db, owner_id=user.id, is_active=True
        )
        
        # Проверяем, есть ли уже такое устройство
        device_exists = any(device.device_id == device_id for device in devices)
        
        # Если устройство уже существует, разрешаем доступ
        if device_exists:
            return {
                "allowed": True, 
                "message": "Device already registered",
                "device_limit": device_limit,
                "current_devices": len(devices)
            }
        
        # Проверяем, не превышен ли лимит
        if len(devices) >= device_limit:
            # Если есть запрос, логируем попытку превышения лимита
            if request:
                logger.warning(
                    f"User {user.id} ({user.email}) reached device limit. "
                    f"Current devices: {len(devices)}, Limit: {device_limit}"
                )
            
            # Возвращаем ошибку с сообщением
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": self.max_devices_message,
                    "code": "device_limit_reached",
                    "device_limit": device_limit,
                    "current_devices": len(devices)
                }
            )
        
        return {
            "allowed": True,
            "message": "Device limit not reached",
            "device_limit": device_limit,
            "current_devices": len(devices) + 1  # +1 для нового устройства
        }
    
    async def register_device(
        self,
        db: AsyncSession,
        user: User,
        device_id: str,
        device_info: Dict[str, Any],
        request: Optional[Request] = None
    ) -> Device:
        """
        Регистрирует новое устройство для пользователя.
        
        Args:
            db: Асинхронная сессия БД
            user: Пользователь
            device_id: Идентификатор устройства
            device_info: Информация об устройстве
            request: FastAPI Request объект (опционально)
            
        Returns:
            Device: Зарегистрированное устройство
            
        Raises:
            HTTPException: Если лимит устройств превышен
        """
        # Проверяем лимит устройств
        await self.check_device_limit(db, user, device_id, request)
        
        # Проверяем, не зарегистрировано ли уже это устройство
        existing_device = await crud_device.get_by_device_id(db, device_id=device_id)
        
        if existing_device:
            # Если устройство уже зарегистрировано, обновляем информацию
            return await crud_device.update(
                db, 
                db_obj=existing_device, 
                obj_in={
                    "last_active": datetime.utcnow(),
                    "is_active": True,
                    "ip_address": request.client.host if request and request.client else None,
                    **device_info
                }
            )
        
        # Создаем новое устройство
        device_in = {
            "name": device_info.get("name", "Unnamed Device"),
            "device_id": device_id,
            "device_model": device_info.get("device_model"),
            "os_name": device_info.get("os_name"),
            "os_version": device_info.get("os_version"),
            "app_version": device_info.get("app_version"),
            "ip_address": request.client.host if request and request.client else None,
            "is_active": True,
            "user_id": user.id,
            "metadata": {
                "user_agent": request.headers.get("user-agent") if request else None,
                **device_info.get("metadata", {})
            }
        }
        
        return await crud_device.create(db, obj_in=device_in)
    
    async def get_user_devices(
        self, 
        db: AsyncSession, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Device]:
        """
        Получает список устройств пользователя.
        
        Args:
            db: Асинхронная сессия БД
            user_id: ID пользователя
            skip: Количество пропускаемых записей
            limit: Максимальное количество возвращаемых записей
            
        Returns:
            List[Device]: Список устройств пользователя
        """
        return await crud_device.get_multi_by_owner(
            db, owner_id=user_id, skip=skip, limit=limit
        )
    
    async def remove_device(
        self, 
        db: AsyncSession, 
        device_id: int,
        user: User
    ) -> Device:
        """
        Удаляет устройство пользователя.
        
        Args:
            db: Асинхронная сессия БД
            device_id: ID устройства
            user: Владелец устройства
            
        Returns:
            Device: Удаленное устройство
            
        Raises:
            HTTPException: Если устройство не найдено или пользователь не является владельцем
        """
        device = await crud_device.get(db, id=device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        if device.user_id != user.id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to remove this device"
            )
        
        return await crud_device.remove(db, id=device_id)

# Создаем экземпляр сервиса
device_limit_service = DeviceLimitService()
