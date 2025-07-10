"""
Pydantic схемы для системных событий.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class SystemEventBase(BaseModel):
    """Базовая схема для системного события."""
    level: str = Field(..., description="Уровень события (debug, info, warning, error, critical)")
    message: str = Field(..., description="Сообщение о событии")
    source: str = Field(..., description="Источник события (system, xray, node, user, api, auth)")
    category: Optional[str] = Field(None, description="Категория события")
    user_id: Optional[int] = Field(None, description="ID пользователя")
    node_id: Optional[int] = Field(None, description="ID ноды")
    ip_address: Optional[str] = Field(None, description="IP-адрес")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали")
    
    @validator('level')
    def validate_level(cls, v):
        """Валидация уровня события."""
        allowed_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if v.lower() not in allowed_levels:
            raise ValueError(f'Уровень должен быть одним из: {", ".join(allowed_levels)}')
        return v.lower()
    
    @validator('source')
    def validate_source(cls, v):
        """Валидация источника события."""
        allowed_sources = ['system', 'xray', 'node', 'user', 'api', 'auth', 'vpn', 'config', 'monitor']
        if v.lower() not in allowed_sources:
            raise ValueError(f'Источник должен быть одним из: {", ".join(allowed_sources)}')
        return v.lower()


class SystemEventCreate(SystemEventBase):
    """Схема для создания системного события."""
    pass


class SystemEventUpdate(BaseModel):
    """Схема для обновления системного события."""
    level: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = None
    node_id: Optional[int] = None
    ip_address: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SystemEvent(SystemEventBase):
    """Схема для возврата системного события."""
    id: int
    uuid: str
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class SystemEventInDB(SystemEvent):
    """Схема для системного события в базе данных."""
    pass


class SystemEventResponse(BaseModel):
    """Схема ответа для списка событий."""
    events: list[SystemEvent]
    total: int
    page: int
    limit: int


class SystemEventStats(BaseModel):
    """Схема для статистики событий."""
    by_level: Dict[str, int] = Field(..., description="Количество событий по уровням")
    by_source: Dict[str, int] = Field(..., description="Количество событий по источникам")
    total_events: int = Field(..., description="Общее количество событий")
    error_events: int = Field(..., description="Количество событий с ошибками")
    time_range_hours: int = Field(..., description="Временной диапазон в часах")


class SystemEventFilter(BaseModel):
    """Схема для фильтрации событий."""
    level: Optional[str] = Field(None, description="Фильтр по уровню")
    source: Optional[str] = Field(None, description="Фильтр по источнику")
    category: Optional[str] = Field(None, description="Фильтр по категории")
    user_id: Optional[int] = Field(None, description="Фильтр по пользователю")
    node_id: Optional[int] = Field(None, description="Фильтр по ноде")
    hours_back: int = Field(24, ge=1, le=168, description="Количество часов назад (1-168)")
    limit: int = Field(50, ge=1, le=1000, description="Максимальное количество событий")
    page: int = Field(0, ge=0, description="Номер страницы")


class CreateSystemEventRequest(BaseModel):
    """Схема запроса для создания события через API."""
    level: str = Field(..., description="Уровень события")
    message: str = Field(..., description="Сообщение о событии")
    source: str = Field(..., description="Источник события")
    category: Optional[str] = Field(None, description="Категория события")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали")


class SystemEventSummary(BaseModel):
    """Краткая сводка по событиям."""
    recent_errors: int = Field(..., description="Количество недавних ошибок")
    recent_warnings: int = Field(..., description="Количество недавних предупреждений")
    system_health: str = Field(..., description="Общее состояние системы (good, warning, critical)")
    last_error: Optional[SystemEvent] = Field(None, description="Последняя ошибка")
    last_critical: Optional[SystemEvent] = Field(None, description="Последнее критическое событие")