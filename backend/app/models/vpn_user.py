"""
Модель пользователя VPN.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

import uuid

from ..database import Base
from .types import UUID


class VPNUserStatus(str, Enum):
    """Статусы пользователя VPN."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    DISABLED = "disabled"


class VPNUser(Base):
    """Модель пользователя VPN."""
    __tablename__ = "vpn_users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(), default=uuid.uuid4, unique=True, index=True)
    
    # Основная информация
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Статус и активность
    status = Column(SQLEnum(VPNUserStatus), default=VPNUserStatus.ACTIVE, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Лимиты трафика
    traffic_limit = Column(BigInteger, default=0, nullable=False, comment="Лимит трафика в байтах, 0 = безлимит")
    upload_traffic = Column(BigInteger, default=0, nullable=False, comment="Использованный исходящий трафик в байтах")
    download_traffic = Column(BigInteger, default=0, nullable=False, comment="Использованный входящий трафик в байтах")
    
    # Временные ограничения
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="Дата истечения доступа")
    last_active_at = Column(DateTime(timezone=True), nullable=True, comment="Время последней активности")
    
    # Настройки протоколов
    xtls_enabled = Column(Boolean, default=False, nullable=False, comment="Включен ли XTLS")
    
    # Связи с основным пользователем
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="ID основного пользователя системы")
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Связи
    user = relationship("User", back_populates="vpn_users")
    devices = relationship("Device", back_populates="vpn_user")
    
    def __repr__(self) -> str:
        return f"<VPNUser {self.username} ({self.email})>"
    
    @property
    def total_traffic(self) -> int:
        """Общий использованный трафик в байтах."""
        return self.upload_traffic + self.download_traffic
    
    @property
    def traffic_remaining(self) -> Optional[int]:
        """Оставшийся трафик в байтах. None если безлимит."""
        if self.traffic_limit == 0:
            return None
        return max(0, self.traffic_limit - self.total_traffic)
    
    @property
    def is_traffic_exceeded(self) -> bool:
        """Превышен ли лимит трафика."""
        if self.traffic_limit == 0:
            return False
        return self.total_traffic >= self.traffic_limit
    
    @property
    def is_expired(self) -> bool:
        """Истек ли срок действия аккаунта."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_online(self) -> bool:
        """Был ли пользователь активен в последние 5 минут."""
        if not self.last_active_at:
            return False
        return (datetime.utcnow() - self.last_active_at).total_seconds() < 300
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь."""
        return {
            "id": self.id,
            "uuid": str(self.uuid),
            "username": self.username,
            "email": self.email,
            "status": self.status.value if self.status else None,
            "is_active": self.is_active,
            "traffic_limit": self.traffic_limit,
            "upload_traffic": self.upload_traffic,
            "download_traffic": self.download_traffic,
            "total_traffic": self.total_traffic,
            "traffic_remaining": self.traffic_remaining,
            "is_traffic_exceeded": self.is_traffic_exceeded,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "is_expired": self.is_expired,
            "is_online": self.is_online,
            "xtls_enabled": self.xtls_enabled,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }