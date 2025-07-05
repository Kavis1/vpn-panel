"""
Сервис для управления устройствами пользователей.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import hashlib

from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.device import Device

logger = logging.getLogger(__name__)

class DeviceService:
    """
    Сервис для управления устройствами пользователей.
    Включает функционал ограничения устройств по HWID, вдохновленный Remnawave.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hwid_enabled = getattr(settings, "HWID_DEVICE_LIMIT_ENABLED", False)
        self.fallback_device_limit = getattr(settings, "HWID_FALLBACK_DEVICE_LIMIT", 5)
        self.max_devices_message = getattr(
            settings, 
            "HWID_MAX_DEVICES_ANNOUNCE", 
            "Вы достигли максимального количества разрешенных устройств для вашей подписки."
        )
    
    def generate_device_id(self, request: Request, user_agent: str) -> str:
        """
        Сгенерировать уникальный идентификатор устройства на основе запроса.
        
        Args:
            request: Запрос от клиента
            user_agent: User-Agent строка
            
        Returns:
            Уникальный идентификатор устройства (хеш)
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
        user_id: int, 
        device_id: str, 
        request: Optional[Request] = None
    ) -> bool:
        """
        Проверить, не превышен ли лимит устройств для пользователя.
        
        Args:
            user_id: ID пользователя
            device_id: Идентификатор устройства
            request: Запрос (опционально, для логирования)
            
        Returns:
            True, если лимит не превышен, иначе False
            
        Raises:
            HTTPException: Если лимит устройств превышен
        """
        if not self.hwid_enabled:
            return True
            
        # Получаем лимит устройств для пользователя (или используем значение по умолчанию)
        user = await crud.user.get(self.db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
            
        device_limit = getattr(user, "device_limit", self.fallback_device_limit)
        
        # Если лимит не установлен или равен 0, пропускаем проверку
        if not device_limit or device_limit <= 0:
            return True
        
        # Получаем все активные устройства пользователя
        devices = await crud.device.get_multi_by_owner(
            self.db, user_id=user_id, is_active=True
        )
        
        # Проверяем, есть ли уже такое устройство
        device_exists = any(device.device_id == device_id for device in devices)
        
        # Если устройство уже существует, разрешаем доступ
        if device_exists:
            return True
        
        # Проверяем, не превышен ли лимит
        if len(devices) >= device_limit:
            # Если есть запрос, логируем попытку превышения лимита
            if request:
                logger.warning(
                    f"Пользователь {user.id} ({user.email}) достиг лимита устройств. "
                    f"Текущие устройства: {len(devices)}, Лимит: {device_limit}"
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
        
        return True
    
    async def register_device(
        self,
        device_in: schemas.DeviceCreate,
        user: models.User,
        ip_address: Optional[str] = None,
        request: Optional[Request] = None
    ) -> schemas.Device:
        """
        Зарегистрировать новое устройство или обновить существующее.
        
        Args:
            device_in: Данные устройства
            user: Пользователь-владелец
            ip_address: IP-адрес устройства
            request: Запрос (опционально, для проверки лимита устройств)
            
        Returns:
            Зарегистрированное устройство
            
        Raises:
            HTTPException: Если устройство не может быть зарегистрировано
        """
        try:
            # Проверяем лимит устройств, если включено
            if self.hwid_enabled and request:
                await self.check_device_limit(user.id, device_in.device_id, request)
            
            # Проверяем, зарегистрировано ли уже устройство
            device = await crud.device.get_by_device_id(
                self.db, device_id=device_in.device_id
            )
            
            if device:
                # Устройство уже зарегистрировано, обновляем информацию
                device = await crud.device.update(
                    self.db,
                    db_obj=device,
                    obj_in={
                        "name": device_in.name,
                        "device_model": device_in.device_model,
                        "os_name": device_in.os_name,
                        "os_version": device_in.os_version,
                        "app_version": device_in.app_version,
                        "ip_address": ip_address or device.ip_address,
                        "last_active": datetime.utcnow(),
                        "is_active": True,
                        "metadata": {**device.metadata_, **device_in.metadata}
                    }
                )
            else:
                # Создаем новое устройство
                device_data = device_in.dict()
                device_data["user_id"] = user.id
                device_data["ip_address"] = ip_address
                device_data["created_at"] = datetime.utcnow()
                device_data["last_active"] = datetime.utcnow()
                device_data["is_active"] = True
                
                # Если это первое устройство пользователя, помечаем его как доверенное
                if len(user_devices) == 0:
                    device_data["is_trusted"] = True
                
                device = await crud.device.create(self.db, obj_in=device_data)
            
            await self.db.commit()
            await self.db.refresh(device)
            
            return schemas.Device.from_orm(device)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при регистрации устройства: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось зарегистрировать устройство"
            )
    
    async def get_user_devices(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> Tuple[List[schemas.Device], int, Dict[str, Any]]:
        """
        Получить список устройств пользователя с информацией о лимитах.
        
        Args:
            user_id: ID пользователя
            skip: Количество пропускаемых записей
            limit: Максимальное количество возвращаемых записей
            include_inactive: Включать ли неактивные устройства
            
        Returns:
            Кортеж (список устройств, общее количество, информация о лимитах)
        """
        try:
            # Получаем устройства пользователя
            filter_params = {"user_id": user_id}
            if not include_inactive:
                filter_params["is_active"] = True
                
            devices = await crud.device.get_multi_by_owner(
                self.db, 
                user_id=user_id, 
                skip=skip, 
                limit=limit,
                filter_params=filter_params
            )
            
            total = await crud.device.count(
                self.db, filter_params=filter_params
            )
            
            # Получаем информацию о лимитах
            user = await crud.user.get(self.db, id=user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден"
                )
                
            device_limit = getattr(user, "device_limit", self.fallback_device_limit)
            
            limit_info = {
                "limit_enabled": self.hwid_enabled,
                "device_limit": device_limit,
                "current_devices": total,
                "can_add_more": not self.hwid_enabled or device_limit <= 0 or total < device_limit,
                "message": self.max_devices_message if self.hwid_enabled and device_limit > 0 and total >= device_limit else None
            }
            
            return [schemas.Device.from_orm(device) for device in devices], total, limit_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении списка устройств: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось получить список устройств"
            )
    
    async def get_device(
        self, device_id: int, user: models.User, check_owner: bool = True
    ) -> Optional[schemas.Device]:
        """
        Получить информацию об устройстве.
        
        Args:
            device_id: ID устройства
            user: Текущий пользователь
            check_owner: Проверять ли владельца устройства
            
        Returns:
            Информация об устройстве или None, если устройство не найдено
            
        Raises:
            HTTPException: Если доступ запрещен
        """
        try:
            device = await crud.device.get(self.db, id=device_id)
            
            if not device:
                return None
                
            # Проверяем права доступа
            if check_owner and device.user_id != user.id and not user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для доступа к этому устройству"
                )
                
            return schemas.Device.from_orm(device)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении устройства: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось получить информацию об устройстве"
            )
    
    async def update_device(
        self,
        device_id: int,
        device_in: schemas.DeviceUpdate,
        user: models.User
    ) -> Optional[schemas.Device]:
        """
        Обновить информацию об устройстве.
        
        Args:
            device_id: ID устройства
            device_in: Новые данные устройства
            user: Текущий пользователь
            
        Returns:
            Обновленная информация об устройстве или None, если устройство не найдено
            
        Raises:
            HTTPException: Если доступ запрещен или произошла ошибка
        """
        try:
            device = await crud.device.get(self.db, id=device_id)
            
            if not device:
                return None
                
            # Проверяем права доступа
            if device.user_id != user.id and not user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для обновления этого устройства"
                )
            
            # Обновляем данные устройства
            update_data = device_in.dict(exclude_unset=True)
            
            # Обновляем время последней активности
            update_data["last_active"] = datetime.utcnow()
            
            device = await crud.device.update(
                self.db, db_obj=device, obj_in=update_data
            )
            
            await self.db.commit()
            await self.db.refresh(device)
            
            return schemas.Device.from_orm(device)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при обновлении устройства: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось обновить информацию об устройстве"
            )
    
    async def delete_device(
        self, device_id: int, user: models.User
    ) -> Optional[schemas.Device]:
        """
        Удалить устройство.
        
        Args:
            device_id: ID устройства
            user: Текущий пользователь
            
        Returns:
            Удаленное устройство или None, если устройство не найдено
            
        Raises:
            HTTPException: Если доступ запрещен или произошла ошибка
        """
        try:
            device = await crud.device.get(self.db, id=device_id)
            
            if not device:
                return None
                
            # Проверяем права доступа
            if device.user_id != user.id and not user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для удаления этого устройства"
                )
            
            # Удаляем устройство
            await crud.device.remove(self.db, id=device_id)
            await self.db.commit()
            
            return schemas.Device.from_orm(device)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при удалении устройства: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось удалить устройство"
            )
    
    async def revoke_device(
        self, device_id: int, user: models.User
    ) -> Optional[schemas.Device]:
        """
        Отозвать устройство (деактивировать).
        
        Args:
            device_id: ID устройства
            user: Текущий пользователь
            
        Returns:
            Обновленное устройство или None, если устройство не найдено
            
        Raises:
            HTTPException: Если доступ запрещен или произошла ошибка
        """
        try:
            device = await crud.device.revoke_device(
                self.db, device_id=device_id, current_user=user
            )
            
            if not device:
                return None
                
            await self.db.commit()
            await self.db.refresh(device)
            
            return schemas.Device.from_orm(device)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при отзыве устройства: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отозвать устройство"
            )
    
    async def trust_device(
        self, device_id: int, trusted: bool, user: models.User
    ) -> Optional[schemas.Device]:
        """
        Пометить устройство как доверенное или наоборот.
        
        Args:
            device_id: ID устройства
            trusted: Сделать устройство доверенным (True) или нет (False)
            user: Текущий пользователь
            
        Returns:
            Обновленное устройство или None, если устройство не найдено
            
        Raises:
            HTTPException: Если доступ запрещен или произошла ошибка
        """
        try:
            device = await crud.device.trust_device(
                self.db, device_id=device_id, trusted=trusted, current_user=user
            )
            
            if not device:
                return None
                
            await self.db.commit()
            await self.db.refresh(device)
            
            return schemas.Device.from_orm(device)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Ошибка при изменении статуса доверия устройства: {str(e)}",
                exc_info=True
            )
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось изменить статус доверия устройства"
            )
    
    async def get_device_stats(
        self, user_id: Optional[int] = None
    ) -> schemas.DeviceStats:
        """
        Получить статистику по устройствам.
        
        Args:
            user_id: ID пользователя (опционально)
            
        Returns:
            Статистика по устройствам
            
        Raises:
            HTTPException: Если произошла ошибка
        """
        try:
            if user_id is not None:
                return await crud.device.get_user_devices_stats(self.db, user_id=user_id)
            else:
                # Получаем общую статистику по всем устройствам
                total_devices = await crud.device.count(self.db)
                active_devices = await crud.device.count(
                    self.db, filter_params={"is_active": True}
                )
                
                # Получаем онлайн-устройства (были активны в последние 5 минут)
                five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
                online_devices = await crud.device.count(
                    self.db,
                    filter_params={
                        "is_active": True,
                        "last_active__gte": five_minutes_ago
                    }
                )
                
                trusted_devices = await crud.device.count(
                    self.db, filter_params={"is_trusted": True}
                )
                
                # Группируем по ОС и моделям (упрощенный вариант)
                devices = await crud.device.get_multi(self.db, limit=1000)
                
                os_stats = {}
                model_stats = {}
                
                for device in devices:
                    if device.os_name:
                        os_stats[device.os_name] = os_stats.get(device.os_name, 0) + 1
                    if device.device_model:
                        model_stats[device.device_model] = model_stats.get(device.device_model, 0) + 1
                
                return schemas.DeviceStats(
                    total_devices=total_devices,
                    active_devices=active_devices,
                    online_devices=online_devices,
                    trusted_devices=trusted_devices,
                    devices_by_os=os_stats,
                    devices_by_model=model_stats
                )
                
        except Exception as e:
            logger.error(f"Ошибка при получении статистики устройств: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось получить статистику устройств"
            )
