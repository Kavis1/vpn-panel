"""
Модель для хранения версий конфигурации Xray.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey

from sqlalchemy.orm import relationship

from ..database import Base

class ConfigVersion(Base):
    """Модель версии конфигурации Xray."""
    __tablename__ = "config_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, index=True, nullable=False, comment="Версия конфигурации")
    description = Column(Text, nullable=True, comment="Описание изменений")
    config = Column(JSON, nullable=False, comment="Конфигурация в формате JSON")
    checksum = Column(String(64), nullable=False, index=True, comment="Контрольная сумма конфигурации")
    is_active = Column(Boolean, default=True, comment="Активна ли эта версия")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Дата создания")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Дата обновления")
    
    # Связи
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="ID пользователя, создавшего версию")
    
    # Отношения
    created_by = relationship("User", back_populates="created_configs")
    syncs = relationship("ConfigSync", back_populates="config_version", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<ConfigVersion {self.version} ({'active' if self.is_active else 'inactive'})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь."""
        return {
            "id": self.id,
            "version": self.version,
            "description": self.description,
            "config": self.config,
            "checksum": self.checksum,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_id": self.created_by_id
        }
