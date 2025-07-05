"""
CRUD-операции для управления конфигурациями Xray.
"""
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.config_version import ConfigVersion
from app.models.config_sync import ConfigSync, SyncStatus
from app.models.node import Node, NodeStatus

class CRUDConfig(CRUDBase[ConfigVersion, schemas.ConfigCreate, schemas.ConfigUpdate]):
    """CRUD-операции для управления конфигурациями Xray."""
    
    async def get_by_version(
        self, db: AsyncSession, *, version: str
    ) -> Optional[ConfigVersion]:
        """Получить конфигурацию по версии."""
        result = await db.execute(
            select(self.model).filter(self.model.version == version)
        )
        return result.scalars().first()
    
    async def get_active_config(self, db: AsyncSession) -> Optional[ConfigVersion]:
        """Получить активную конфигурацию."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.is_active.is_(True))
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()
    
    async def get_default_config(self, db: AsyncSession) -> Optional[ConfigVersion]:
        """Получить конфигурацию по умолчанию."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.is_default.is_(True))
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()
    
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: schemas.ConfigCreate, owner_id: int
    ) -> ConfigVersion:
        """Создать новую конфигурацию."""
        # Генерируем контрольную сумму конфигурации
        config_json = json.dumps(obj_in.config, sort_keys=True)
        checksum = hashlib.sha256(config_json.encode()).hexdigest()
        
        # Проверяем, существует ли уже конфигурация с такой контрольной суммой
        existing_config = await self.get_by_checksum(db, checksum=checksum)
        if existing_config:
            return existing_config
        
        # Если это первая конфигурация, делаем её активной и по умолчанию
        count = await self.count(db)
        is_first = count == 0
        
        # Создаем объект конфигурации
        db_obj = ConfigVersion(
            version=obj_in.version,
            description=obj_in.description,
            config=obj_in.config,
            checksum=checksum,
            status=obj_in.status,
            is_active=is_first or obj_in.is_default,
            is_default=is_first or obj_in.is_default,
            created_by_id=owner_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Если новая конфигурация помечена как активная, деактивируем старую
        if db_obj.is_active:
            await self.deactivate_all(db, exclude_id=db_obj.id)
        
        # Если новая конфигурация помечена как конфигурация по умолчанию,
        # снимаем этот флаг с других конфигураций
        if db_obj.is_default:
            await self.unset_default_flag(db, exclude_id=db_obj.id)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def update_config(
        self, db: AsyncSession, *, db_obj: ConfigVersion, obj_in: Union[schemas.ConfigUpdate, Dict[str, Any]]
    ) -> ConfigVersion:
        """Обновить конфигурацию."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        # Если обновляется конфигурация, пересчитываем контрольную сумму
        if 'config' in update_data:
            config_json = json.dumps(update_data['config'], sort_keys=True)
            update_data['checksum'] = hashlib.sha256(config_json.encode()).hexdigest()
        
        # Обновляем объект
        db_obj = await super().update(db, db_obj=db_obj, obj_in=update_data)
        
        # Если конфигурация помечена как активная, деактивируем остальные
        if db_obj.is_active:
            await self.deactivate_all(db, exclude_id=db_obj.id)
        
        # Если конфигурация помечена как конфигурация по умолчанию,
        # снимаем этот флаг с других конфигураций
        if db_obj.is_default:
            await self.unset_default_flag(db, exclude_id=db_obj.id)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def deactivate_all(
        self, db: AsyncSession, *, exclude_id: Optional[int] = None
    ) -> None:
        """Деактивировать все конфигурации, кроме указанной."""
        query = update(ConfigVersion).where(ConfigVersion.is_active.is_(True))
        
        if exclude_id is not None:
            query = query.where(ConfigVersion.id != exclude_id)
        
        await db.execute(
            query.values(is_active=False, updated_at=datetime.utcnow())
        )
        await db.commit()
    
    async def unset_default_flag(
        self, db: AsyncSession, *, exclude_id: Optional[int] = None
    ) -> None:
        """Снять флаг конфигурации по умолчанию со всех конфигураций, кроме указанной."""
        query = update(ConfigVersion).where(ConfigVersion.is_default.is_(True))
        
        if exclude_id is not None:
            query = query.where(ConfigVersion.id != exclude_id)
        
        await db.execute(
            query.values(is_default=False, updated_at=datetime.utcnow())
        )
        await db.commit()
    
    async def get_by_checksum(
        self, db: AsyncSession, *, checksum: str
    ) -> Optional[ConfigVersion]:
        """Получить конфигурацию по контрольной сумме."""
        result = await db.execute(
            select(self.model).filter(self.model.checksum == checksum)
        )
        return result.scalars().first()
    
    async def get_sync_status(
        self, db: AsyncSession, *, config_id: int, node_id: Optional[int] = None
    ) -> List[ConfigSync]:
        """Получить статус синхронизации конфигурации."""
        query = select(ConfigSync).filter(ConfigSync.config_version_id == config_id)
        
        if node_id is not None:
            query = query.filter(ConfigSync.node_id == node_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create_sync_status(
        self, db: AsyncSession, *, config_id: int, node_id: int, status: SyncStatus = SyncStatus.PENDING
    ) -> ConfigSync:
        """Создать запись о статусе синхронизации."""
        db_obj = ConfigSync(
            config_version_id=config_id,
            node_id=node_id,
            status=status,
            last_attempt=datetime.utcnow(),
            retry_count=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def update_sync_status(
        self,
        db: AsyncSession,
        *,
        sync_id: int,
        status: SyncStatus,
        error_message: Optional[str] = None,
        increment_retry: bool = False
    ) -> Optional[ConfigSync]:
        """Обновить статус синхронизации."""
        db_obj = await db.get(ConfigSync, sync_id)
        
        if not db_obj:
            return None
        
        db_obj.status = status
        db_obj.last_attempt = datetime.utcnow()
        
        if status == SyncStatus.COMPLETED:
            db_obj.last_sync = datetime.utcnow()
            db_obj.error_message = None
            db_obj.retry_count = 0
        elif status == SyncStatus.FAILED:
            db_obj.error_message = error_message
            if increment_retry:
                db_obj.retry_count += 1
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def get_nodes_needing_sync(
        self, db: AsyncSession, *, config_id: int, limit: int = 100
    ) -> List[Node]:
        """Получить список нод, которым требуется синхронизация конфигурации."""
        # Подзапрос для получения последнего статуса синхронизации для каждой ноды
        subq = (
            select(
                ConfigSync.node_id,
                func.max(ConfigSync.id).label('latest_sync_id')
            )
            .filter(ConfigSync.config_version_id == config_id)
            .group_by(ConfigSync.node_id)
            .subquery()
        )
        
        # Запрос для получения нод, которые:
        # 1. Имеют статус синхронизации, отличный от COMPLETED
        # 2. Или не имеют записей о синхронизации для этой конфигурации
        result = await db.execute(
            select(Node)
            .outerjoin(
                subq,
                Node.id == subq.c.node_id
            )
            .outerjoin(
                ConfigSync,
                ConfigSync.id == subq.c.latest_sync_id
            )
            .where(
                or_(
                    ConfigSync.id.is_(None),  # Нет записей о синхронизации
                    ConfigSync.status != SyncStatus.COMPLETED,  # Синхронизация не завершена
                    ConfigSync.updated_at < datetime.utcnow() - timedelta(hours=24)  # Устаревшая синхронизация
                )
            )
            .filter(Node.is_active.is_(True))  # Только активные ноды
            .order_by(
                Node.priority.asc(),
                Node.updated_at.asc()
            )
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_config_sync_summary(
        self, db: AsyncSession, *, config_id: int
    ) -> Dict[str, Any]:
        """Получить сводную информацию о синхронизации конфигурации."""
        # Получаем общее количество нод
        total_nodes = await db.scalar(
            select(func.count(Node.id)).filter(Node.is_active.is_(True))
        )
        
        if total_nodes == 0:
            return {
                "total_nodes": 0,
                "synced_nodes": 0,
                "pending_nodes": 0,
                "failed_nodes": 0,
                "outdated_nodes": 0,
                "sync_status": "no_nodes"
            }
        
        # Получаем количество нод с разными статусами синхронизации
        result = await db.execute(
            select(
                ConfigSync.status,
                func.count(ConfigSync.id).label('count')
            )
            .select_from(ConfigSync)
            .join(
                Node,
                Node.id == ConfigSync.node_id
            )
            .where(
                ConfigSync.config_version_id == config_id,
                Node.is_active.is_(True)
            )
            .group_by(ConfigSync.status)
        )
        
        status_counts = {row[0]: row[1] for row in result.all()}
        
        # Вычисляем количество синхронизированных нод
        synced_nodes = status_counts.get(SyncStatus.COMPLETED, 0)
        pending_nodes = status_counts.get(SyncStatus.PENDING, 0) + status_counts.get(SyncStatus.IN_PROGRESS, 0)
        failed_nodes = status_counts.get(SyncStatus.FAILED, 0)
        outdated_nodes = status_counts.get(SyncStatus.OUTDATED, 0)
        
        # Определяем общий статус синхронизации
        if synced_nodes == total_nodes:
            sync_status = "completed"
        elif failed_nodes > 0:
            sync_status = "failed"
        elif pending_nodes > 0:
            sync_status = "in_progress"
        else:
            sync_status = "unknown"
        
        return {
            "total_nodes": total_nodes,
            "synced_nodes": synced_nodes,
            "pending_nodes": pending_nodes,
            "failed_nodes": failed_nodes,
            "outdated_nodes": outdated_nodes,
            "sync_status": sync_status
        }

# Создаем экземпляр CRUD-класса
config = CRUDConfig(ConfigVersion)
