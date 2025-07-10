"""
Тесты для системы событий (SystemEvent).
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_event import SystemEvent, SystemEventLevel, SystemEventSource
from app.crud.crud_system_event import system_event
from app.schemas.system_event import SystemEventCreate


class TestSystemEvent:
    """Тесты для модели SystemEvent."""
    
    def test_create_event_class_method(self):
        """Тест создания события через класс-метод."""
        event = SystemEvent.create_event(
            level=SystemEventLevel.INFO,
            message="Тестовое событие",
            source=SystemEventSource.SYSTEM,
            category="test",
            details={"test": True}
        )
        
        assert event.level == SystemEventLevel.INFO
        assert event.message == "Тестовое событие"
        assert event.source == SystemEventSource.SYSTEM
        assert event.category == "test"
        assert event.details == {"test": True}
    
    def test_to_dict_method(self):
        """Тест преобразования события в словарь."""
        event = SystemEvent.create_event(
            level=SystemEventLevel.ERROR,
            message="Ошибка системы",
            source=SystemEventSource.API
        )
        event.id = 1
        event.timestamp = datetime.utcnow()
        event.created_at = datetime.utcnow()
        
        result = event.to_dict()
        
        assert result["id"] == 1
        assert result["level"] == SystemEventLevel.ERROR
        assert result["message"] == "Ошибка системы"
        assert result["source"] == SystemEventSource.API
        assert "timestamp" in result
        assert "created_at" in result


@pytest.mark.asyncio
class TestSystemEventCRUD:
    """Тесты для CRUD операций SystemEvent."""
    
    async def test_create_event(self, db_session: AsyncSession):
        """Тест создания события через CRUD."""
        event = await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.INFO,
            message="Тестовое CRUD событие",
            source=SystemEventSource.SYSTEM,
            category="test"
        )
        
        assert event.id is not None
        assert event.level == SystemEventLevel.INFO
        assert event.message == "Тестовое CRUD событие"
        assert event.source == SystemEventSource.SYSTEM
        assert event.category == "test"
    
    async def test_get_recent_events(self, db_session: AsyncSession):
        """Тест получения последних событий."""
        # Создаем несколько тестовых событий
        for i in range(5):
            await system_event.create_event(
                db=db_session,
                level=SystemEventLevel.INFO,
                message=f"Событие {i}",
                source=SystemEventSource.SYSTEM
            )
        
        # Получаем последние события
        events = await system_event.get_recent_events(
            db=db_session,
            limit=3
        )
        
        assert len(events) <= 3
        # События должны быть отсортированы по времени (новые первыми)
        if len(events) > 1:
            assert events[0].timestamp >= events[1].timestamp
    
    async def test_get_events_count_by_level(self, db_session: AsyncSession):
        """Тест подсчета событий по уровням."""
        # Создаем события разных уровней
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.INFO,
            message="Info событие",
            source=SystemEventSource.SYSTEM
        )
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.ERROR,
            message="Error событие",
            source=SystemEventSource.SYSTEM
        )
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.ERROR,
            message="Еще одно Error событие",
            source=SystemEventSource.SYSTEM
        )
        
        # Получаем статистику
        counts = await system_event.get_events_count_by_level(db=db_session)
        
        assert counts.get(SystemEventLevel.INFO, 0) >= 1
        assert counts.get(SystemEventLevel.ERROR, 0) >= 2
    
    async def test_get_events_count_by_source(self, db_session: AsyncSession):
        """Тест подсчета событий по источникам."""
        # Создаем события от разных источников
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.INFO,
            message="Системное событие",
            source=SystemEventSource.SYSTEM
        )
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.INFO,
            message="API событие",
            source=SystemEventSource.API
        )
        
        # Получаем статистику
        counts = await system_event.get_events_count_by_source(db=db_session)
        
        assert counts.get(SystemEventSource.SYSTEM, 0) >= 1
        assert counts.get(SystemEventSource.API, 0) >= 1
    
    async def test_get_error_events(self, db_session: AsyncSession):
        """Тест получения событий с ошибками."""
        # Создаем события разных уровней
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.INFO,
            message="Обычное событие",
            source=SystemEventSource.SYSTEM
        )
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.ERROR,
            message="Событие с ошибкой",
            source=SystemEventSource.SYSTEM
        )
        await system_event.create_event(
            db=db_session,
            level=SystemEventLevel.CRITICAL,
            message="Критическое событие",
            source=SystemEventSource.SYSTEM
        )
        
        # Получаем только события с ошибками
        error_events = await system_event.get_error_events(db=db_session)
        
        # Все события должны быть уровня ERROR или CRITICAL
        for event in error_events:
            assert event.level in [SystemEventLevel.ERROR, SystemEventLevel.CRITICAL]


class TestSystemEventConstants:
    """Тесты для констант SystemEvent."""
    
    def test_event_levels(self):
        """Тест констант уровней событий."""
        assert SystemEventLevel.DEBUG == "debug"
        assert SystemEventLevel.INFO == "info"
        assert SystemEventLevel.WARNING == "warning"
        assert SystemEventLevel.ERROR == "error"
        assert SystemEventLevel.CRITICAL == "critical"
    
    def test_event_sources(self):
        """Тест констант источников событий."""
        assert SystemEventSource.SYSTEM == "system"
        assert SystemEventSource.XRAY == "xray"
        assert SystemEventSource.NODE == "node"
        assert SystemEventSource.USER == "user"
        assert SystemEventSource.API == "api"
        assert SystemEventSource.AUTH == "auth"