"""
Модель для хранения информации об устройствах пользователей.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User  # noqa: F401
    from .vpn_user import VPNUser  # noqa: F401

class Device(Base):
    """Модель устройства пользователя."""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="Название устройства, задаваемое пользователем")
    device_id = Column(String(255), unique=True, index=True, nullable=False, comment="Уникальный идентификатор устройства")
    device_model = Column(String(100), comment="Модель устройства")
    os_name = Column(String(50), comment="Название ОС")
    os_version = Column(String(50), comment="Версия ОС")
    app_version = Column(String(50), comment="Версия приложения")
    ip_address = Column(String(45), comment="IP-адрес устройства")
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Время последней активности")
    is_active = Column(Boolean, default=True, comment="Активно ли устройство")
    is_trusted = Column(Boolean, default=False, comment="Доверенное ли устройство")
    metadata_ = Column("metadata", JSON, default={}, comment="Дополнительные метаданные устройства")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Дата создания")
    
    # Связи
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="ID пользователя-владельца")
    vpn_user_id = Column(Integer, ForeignKey("vpn_users.id"), nullable=True, comment="ID VPN-пользователя")
    
    # Отношения
    user = relationship("User", back_populates="devices")
    vpn_user = relationship("VPNUser", back_populates="devices")
    
    def __repr__(self) -> str:
        return f"<Device {self.name} ({self.device_model or 'Unknown'})>"
    
    @property
    def is_online(self) -> bool:
        """Проверяет, активно ли устройство (было в сети не позднее 5 минут назад)."""
        if not self.last_active:
            return False
        return (datetime.utcnow() - self.last_active).total_seconds() < 300  # 5 минут
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "device_id": self.device_id,
            "device_model": self.device_model,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "app_version": self.app_version,
            "ip_address": self.ip_address,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "is_active": self.is_active,
            "is_trusted": self.is_trusted,
            "is_online": self.is_online,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_id": self.user_id,
            "vpn_user_id": self.vpn_user_id,
            "metadata": self.metadata_ or {}
        }
