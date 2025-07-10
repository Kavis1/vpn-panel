"""
CRUD операции для системных событий.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.system_event import SystemEvent, SystemEventLevel, SystemEventSource
from app.schemas.system_event import SystemEventCreate, SystemEventUpdate


class CRUDSystemEvent(CRUDBase[SystemEvent, SystemEventCreate, SystemEventUpdate]):
    """CRUD операции для системных событий."""
    
    async def get_recent_events(
        self,
        db: AsyncSession,
        *,
        limit: int = 50,
        level: Optional[str] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        node_id: Optional[int] = None,
        hours_back: int = 24
    ) -> List[SystemEvent]:
        """
        Получить последние события системы.
        
        Args:
            db: Сессия базы данных
            limit: Максимальное количество событий
            level: Фильтр по уровню события
            source: Фильтр по источнику события
            category: Фильтр по категории события
            user_id: Фильтр по пользователю
            node_id: Фильтр по ноде
            hours_back: Количество часов назад для поиска событий
            
        Returns:
            Список последних событий
        """
        # Базовый запрос
        query = select(self.model).order_by(desc(self.model.timestamp))
        
        # Фильтр по времени
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        query = query.where(self.model.timestamp >= time_threshold)
        
        # Применяем фильтры
        if level:
            query = query.where(self.model.level == level)
        if source:
            query = query.where(self.model.source == source)
        if category:
            query = query.where(self.model.category == category)
        if user_id:
            query = query.where(self.model.user_id == user_id)
        if node_id:
            query = query.where(self.model.node_id == node_id)
            
        # Лимит
        query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_events_by_timerange(
        self,
        db: AsyncSession,
        *,
        start_time: datetime,
        end_time: datetime,
        level: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 1000
    ) -> List[SystemEvent]:
        """
        Получить события за определенный период времени.
        
        Args:
            db: Сессия базы данных
            start_time: Начальное время
            end_time: Конечное время
            level: Фильтр по уровню
            source: Фильтр по источнику
            limit: Максимальное количество событий
            
        Returns:
            Список событий за период
        """
        query = select(self.model).where(
            and_(
                self.model.timestamp >= start_time,
                self.model.timestamp <= end_time
            )
        ).order_by(desc(self.model.timestamp))
        
        if level:
            query = query.where(self.model.level == level)
        if source:
            query = query.where(self.model.source == source)
            
        query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_events_count_by_level(
        self,
        db: AsyncSession,
        *,
        hours_back: int = 24
    ) -> Dict[str, int]:
        """
        Получить количество событий по уровням за последние часы.
        
        Args:
            db: Сессия базы данных
            hours_back: Количество часов назад
            
        Returns:
            Словарь с количеством событий по уровням
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        
        query = select(
            self.model.level,
            func.count(self.model.id).label('count')
        ).where(
            self.model.timestamp >= time_threshold
        ).group_by(self.model.level)
        
        result = await db.execute(query)
        rows = result.all()
        
        return {row.level: row.count for row in rows}
    
    async def get_events_count_by_source(
        self,
        db: AsyncSession,
        *,
        hours_back: int = 24
    ) -> Dict[str, int]:
        """
        Получить количество событий по источникам за последние часы.
        
        Args:
            db: Сессия базы данных
            hours_back: Количество часов назад
            
        Returns:
            Словарь с количеством событий по источникам
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        
        query = select(
            self.model.source,
            func.count(self.model.id).label('count')
        ).where(
            self.model.timestamp >= time_threshold
        ).group_by(self.model.source)
        
        result = await db.execute(query)
        rows = result.all()
        
        return {row.source: row.count for row in rows}
    
    async def create_event(
        self,
        db: AsyncSession,
        *,
        level: str,
        message: str,
        source: str,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        node_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> SystemEvent:
        """
        Создать новое системное событие.
        
        Args:
            db: Сессия базы данных
            level: Уровень события
            message: Сообщение
            source: Источник события
            category: Категория события
            user_id: ID пользователя
            node_id: ID ноды
            ip_address: IP-адрес
            details: Дополнительные детали
            
        Returns:
            Созданное событие
        """
        event = SystemEvent.create_event(
            level=level,
            message=message,
            source=source,
            category=category,
            user_id=user_id,
            node_id=node_id,
            ip_address=ip_address,
            details=details
        )
        
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event
    
    async def cleanup_old_events(
        self,
        db: AsyncSession,
        *,
        days_to_keep: int = 30
    ) -> int:
        """
        Очистить старые события.
        
        Args:
            db: Сессия базы данных
            days_to_keep: Количество дней для хранения событий
            
        Returns:
            Количество удаленных событий
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Подсчитываем количество событий для удаления
        count_query = select(func.count(self.model.id)).where(
            self.model.timestamp < cutoff_date
        )
        count_result = await db.execute(count_query)
        count = count_result.scalar()
        
        # Удаляем старые события
        delete_query = self.model.__table__.delete().where(
            self.model.timestamp < cutoff_date
        )
        await db.execute(delete_query)
        await db.commit()
        
        return count
    
    async def get_error_events(
        self,
        db: AsyncSession,
        *,
        limit: int = 100,
        hours_back: int = 24
    ) -> List[SystemEvent]:
        """
        Получить события с ошибками за последние часы.
        
        Args:
            db: Сессия базы данных
            limit: Максимальное количество событий
            hours_back: Количество часов назад
            
        Returns:
            Список событий с ошибками
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        
        query = select(self.model).where(
            and_(
                self.model.timestamp >= time_threshold,
                self.model.level.in_([SystemEventLevel.ERROR, SystemEventLevel.CRITICAL])
            )
        ).order_by(desc(self.model.timestamp)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()


# Создаем экземпляр CRUD для использования в приложении
system_event = CRUDSystemEvent(SystemEvent)