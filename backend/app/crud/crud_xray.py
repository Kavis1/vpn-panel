from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.xray import XrayConfig, XrayConfigInDB
from app.schemas.xray import XrayConfigCreate, XrayConfigUpdate

class CRUDXrayConfig(CRUDBase[XrayConfig, XrayConfigCreate, XrayConfigUpdate]):
    """
    CRUD операции для работы с конфигурациями Xray
    """
    
    async def get_active_config(self, db: AsyncSession) -> Optional[XrayConfigInDB]:
        """Получение активной конфигурации Xray"""
        result = await db.execute(
            select(XrayConfig).filter(XrayConfig.is_active == True)
        )
        return result.scalars().first()
    
    async def deactivate(self, db: AsyncSession, *, db_obj: XrayConfig) -> XrayConfigInDB:
        """Деактивация конфигурации Xray"""
        db_obj.is_active = False
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_version(self, db: AsyncSession, *, version: str) -> Optional[XrayConfigInDB]:
        """Получение конфигурации по версии"""
        result = await db.execute(
            select(XrayConfig).filter(XrayConfig.version == version)
        )
        return result.scalars().first()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[XrayConfigInDB]:
        """
        Получение списка конфигураций с пагинацией и фильтрацией по активности
        """
        query = select(XrayConfig)
        
        if is_active is not None:
            query = query.filter(XrayConfig.is_active == is_active)
            
        query = query.offset(skip).limit(limit).order_by(XrayConfig.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create_with_owner(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: XrayConfigCreate,
        owner_id: int
    ) -> XrayConfigInDB:
        """Создание конфигурации с указанием владельца"""
        db_obj = XrayConfig(
            **obj_in.dict(),
            created_by=owner_id,
            updated_by=owner_id,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_config(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: XrayConfig, 
        obj_in: XrayConfigUpdate
    ) -> XrayConfigInDB:
        """Обновление конфигурации"""
        update_data = obj_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

# Создаем экземпляр CRUD класса
crud_xray_config = CRUDXrayConfig(XrayConfig)
xray = crud_xray_config  # Алиас для совместимости
