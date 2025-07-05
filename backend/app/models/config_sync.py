"""
Модели для отслеживания синхронизации конфигурации на нодах.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class SyncStatus(str, Enum):
    """Статус синхронизации конфигурации на ноде."""
    PENDING = "pending"      # Ожидает синхронизации
    IN_PROGRESS = "in_progress"  # В процессе синхронизации
    COMPLETED = "completed"  # Синхронизация завершена успешно
    FAILED = "failed"       # Ошибка при синхронизации
    OUTDATED = "outdated"    # Конфигурация устарела

class ConfigSync(Base):
    """Модель для отслеживания состояния синхронизации конфигурации на нодах."""
    __tablename__ = "config_syncs"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, nullable=False, comment="Статус синхронизации")
    last_sync = Column(DateTime, nullable=True, comment="Время последней успешной синхронизации")
    last_attempt = Column(DateTime, nullable=True, comment="Время последней попытки синхронизации")
    error_message = Column(Text, nullable=True, comment="Сообщение об ошибке (если есть)")
    retry_count = Column(Integer, default=0, nullable=False, comment="Количество попыток синхронизации")
    is_active = Column(Boolean, default=True, comment="Активна ли синхронизация")
    metadata_ = Column("metadata", JSONB, default={}, comment="Дополнительные метаданные")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Дата создания")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Дата обновления")
    
    # Связи
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, comment="ID ноды")
    config_version_id = Column(Integer, ForeignKey("config_versions.id"), nullable=False, comment="ID версии конфигурации")
    
    # Отношения
    node = relationship("Node", back_populates="config_syncs")
    config_version = relationship("ConfigVersion", back_populates="syncs")
    
    def __repr__(self) -> str:
        return f"<ConfigSync node={self.node_id} version={self.config_version_id} status={self.status}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь."""
        return {
            "id": self.id,
            "status": self.status.value if self.status else None,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "is_active": self.is_active,
            "metadata": self.metadata_ or {},
            "node_id": self.node_id,
            "config_version_id": self.config_version_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# Добавляем обратные связи в модели Node и ConfigVersion
# В models/node.py добавить:
# config_syncs = relationship("ConfigSync", back_populates="node", cascade="all, delete-orphan")

# В models/config_version.py добавить:
# syncs = relationship("ConfigSync", back_populates="config_version", cascade="all, delete-orphan")
