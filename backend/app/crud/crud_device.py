"""
CRUD-операции для управления устройствами пользователей.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.device import Device

class CRUDDevice(CRUDBase[Device, schemas.DeviceCreate, schemas.DeviceUpdate]):
    """CRUD-операции для управления устройствами."""
    
    async def get_by_device_id(self, db: AsyncSession, device_id: str) -> Optional[Device]:
        """Получить устройство по его уникальному идентификатору."""
        result = await db.execute(
            select(self.model).filter(self.model.device_id == device_id)
        )
        return result.scalars().first()
    
    async def get_multi_by_owner(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Device]:
        """
        Получить список устройств пользователя с пагинацией и фильтрацией.
        
        Args:
            db: Асинхронная сессия БД
            user_id: ID пользователя
            skip: Количество пропускаемых записей
            limit: Максимальное количество возвращаемых записей
            filter_params: Дополнительные параметры фильтрации
            
        Returns:
            Список устройств пользователя
        """
        query = select(self.model).filter(self.model.user_id == user_id)
        
        # Применяем дополнительные фильтры, если они указаны
        if filter_params:
            for key, value in filter_params.items():
                if hasattr(self.model, key):
                    if isinstance(value, bool):
                        query = query.filter(getattr(self.model, key).is_(value))
                    else:
                        query = query.filter(getattr(self.model, key) == value)
        
        # Применяем пагинацию и сортировку
        query = query.offset(skip).limit(limit).order_by(self.model.last_active.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_online_devices(
        self, db: AsyncSession, *, user_id: Optional[int] = None, limit: int = 100
    ) -> List[Device]:
        """Получить список активных (онлайн) устройств."""
        five_minutes_ago = datetime.utcnow() - datetime.timedelta(minutes=5)
        query = select(self.model).filter(
            self.model.last_active >= five_minutes_ago,
            self.model.is_active.is_(True)
        )
        
        if user_id is not None:
            query = query.filter(self.model.user_id == user_id)
        
        query = query.order_by(self.model.last_active.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_last_active(
        self, db: AsyncSession, *, device_id: int, last_active: datetime = None
    ) -> Optional[Device]:
        """Обновить время последней активности устройства."""
        if last_active is None:
            last_active = datetime.utcnow()
            
        result = await db.execute(
            update(self.model)
            .where(self.model.id == device_id)
            .values(last_active=last_active)
            .returning(self.model)
        )
        
        device = result.scalars().first()
        await db.commit()
        return device
    
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: schemas.DeviceCreate, user_id: int
    ) -> Device:
        """Создать новое устройство для пользователя."""
        db_obj = Device(
            **obj_in.dict(exclude={"vpn_user_id" if not hasattr(obj_in, 'vpn_user_id') else None}),
            user_id=user_id,
            vpn_user_id=getattr(obj_in, 'vpn_user_id', None),
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def register_device(
        self,
        db: AsyncSession,
        *,
        device_in: schemas.DeviceCreate,
        user_id: int,
        ip_address: Optional[str] = None,
    ) -> Device:
        """Зарегистрировать новое устройство или обновить существующее."""
        # Проверяем, зарегистрировано ли уже устройство
        device = await self.get_by_device_id(db, device_id=device_in.device_id)
        
        if device:
            # Устройство уже зарегистрировано, обновляем информацию
            update_data = device_in.dict(
                exclude_unset=True,
                exclude={"device_id", "vpn_user_id"}
            )
            
            if ip_address:
                update_data["ip_address"] = ip_address
                
            return await self.update(db, db_obj=device, obj_in=update_data)
        else:
            # Создаем новое устройство
            create_data = device_in.dict()
            if ip_address:
                create_data["ip_address"] = ip_address
                
            return await self.create_with_owner(
                db, obj_in=schemas.DeviceCreate(**create_data), user_id=user_id
            )
    
    async def get_user_devices_stats(
        self, db: AsyncSession, user_id: int
    ) -> schemas.DeviceStats:
        """Получить статистику по устройствам пользователя."""
        # Получаем все устройства пользователя
        devices = await self.get_multi_by_owner(db, user_id=user_id, limit=1000)
        
        # Считаем статистику
        total_devices = len(devices)
        active_devices = sum(1 for d in devices if d.is_active)
        online_devices = sum(1 for d in devices if d.is_online)
        trusted_devices = sum(1 for d in devices if d.is_trusted)
        
        # Группируем по ОС и моделям
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
    
    async def revoke_device(
        self, db: AsyncSession, *, device_id: int, current_user: models.User
    ) -> Optional[Device]:
        """Отозвать устройство (деактивировать)."""
        device = await self.get(db, id=device_id)
        
        if not device:
            return None
            
        # Проверяем права доступа
        if device.user_id != current_user.id and not current_user.is_superuser:
            return None
            
        # Деактивируем устройство
        device.is_active = False
        device.last_active = datetime.utcnow()
        
        db.add(device)
        await db.commit()
        await db.refresh(device)
        
        return device
    
    async def trust_device(
        self, db: AsyncSession, *, device_id: int, trusted: bool, current_user: models.User
    ) -> Optional[Device]:
        """Пометить устройство как доверенное или наоборот."""
        device = await self.get(db, id=device_id)
        
        if not device:
            return None
            
        # Проверяем права доступа
        if device.user_id != current_user.id and not current_user.is_superuser:
            return None
            
        # Обновляем статус доверия
        device.is_trusted = trusted
        device.last_active = datetime.utcnow()
        
        db.add(device)
        await db.commit()
        await db.refresh(device)
        
        return device

# Создаем экземпляр CRUD-класса
device = CRUDDevice(Device)
