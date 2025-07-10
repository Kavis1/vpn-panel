"""
Модель для системных событий и логирования.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Index
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .types import UUID


class SystemEvent(Base):
    """Модель системных событий для логирования и мониторинга."""
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(), default=uuid.uuid4, unique=True, index=True)
    
    # Основная информация о событии
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    level = Column(String(20), nullable=False, index=True)  # debug, info, warning, error, critical
    message = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, index=True)  # system, xray, node, user, api, auth
    
    # Дополнительная информация
    category = Column(String(50), nullable=True, index=True)  # auth, vpn, config, monitoring, etc.
    user_id = Column(Integer, nullable=True, index=True)  # ID пользователя, если событие связано с пользователем
    node_id = Column(Integer, nullable=True, index=True)  # ID ноды, если событие связано с нодой
    ip_address = Column(String(45), nullable=True)  # IP-адрес, если применимо
    
    # Детали события в JSON формате
    details = Column(JSON, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Индексы для оптимизации запросов
    __table_args__ = (
        Index('ix_system_events_timestamp_level', 'timestamp', 'level'),
        Index('ix_system_events_source_category', 'source', 'category'),
        Index('ix_system_events_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_system_events_node_timestamp', 'node_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SystemEvent {self.level}: {self.message[:50]}...>"
    
    @classmethod
    def create_event(
        cls,
        level: str,
        message: str,
        source: str,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        node_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> "SystemEvent":
        """
        Создать новое системное событие.
        
        Args:
            level: Уровень события (debug, info, warning, error, critical)
            message: Сообщение о событии
            source: Источник события (system, xray, node, user, api, auth)
            category: Категория события (auth, vpn, config, monitoring, etc.)
            user_id: ID пользователя (если применимо)
            node_id: ID ноды (если применимо)
            ip_address: IP-адрес (если применимо)
            details: Дополнительные детали в формате JSON
        
        Returns:
            Новый объект SystemEvent
        """
        return cls(
            level=level,
            message=message,
            source=source,
            category=category,
            user_id=user_id,
            node_id=node_id,
            ip_address=ip_address,
            details=details or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать событие в словарь для API ответов."""
        return {
            "id": self.id,
            "uuid": str(self.uuid),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "category": self.category,
            "user_id": self.user_id,
            "node_id": self.node_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SystemEventLevel:
    """Константы для уровней системных событий."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemEventSource:
    """Константы для источников системных событий."""
    SYSTEM = "system"
    XRAY = "xray"
    NODE = "node"
    USER = "user"
    API = "api"
    AUTH = "auth"
    VPN = "vpn"
    CONFIG = "config"
    MONITOR = "monitor"


class SystemEventCategory:
    """Константы для категорий системных событий."""
    AUTH = "auth"
    VPN = "vpn"
    CONFIG = "config"
    MONITORING = "monitoring"
    USER_MANAGEMENT = "user_management"
    NODE_MANAGEMENT = "node_management"
    TRAFFIC = "traffic"
    SECURITY = "security"
    SYSTEM = "system"
    ERROR = "error"