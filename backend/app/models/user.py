from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..database import Base

class User(Base):
    """Модель пользователя системы."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Дополнительные поля
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    telegram_id = Column(String(50), nullable=True, index=True)
    
    # Лимиты и квоты
    data_limit = Column(BigInteger, nullable=True)  # В байтах, None = безлимит
    data_used = Column(BigInteger, default=0)       # Использованный трафик в байтах
    device_limit = Column(Integer, nullable=True)   # Максимальное количество устройств, None = использовать значение по умолчанию
    
    # Срок действия аккаунта
    expire_date = Column(DateTime(timezone=True), nullable=True)
    
    # Настройки уведомлений
    email_notifications = Column(Boolean, default=True)
    telegram_notifications = Column(Boolean, default=False)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    subscriptions = relationship("Subscription", back_populates="user")
    traffic_logs = relationship("TrafficLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def data_remaining(self) -> Optional[int]:
        """Оставшийся трафик в байтах."""
        if self.data_limit is None:
            return None
        return max(0, self.data_limit - self.data_used)
    
    @property
    def is_expired(self) -> bool:
        """Истек ли срок действия аккаунта."""
        if self.expire_date is None:
            return False
        return datetime.utcnow() > self.expire_date
    
    @property
    def is_data_exhausted(self) -> bool:
        """Исчерпан ли лимит трафика."""
        if self.data_limit is None:
            return False
        return self.data_used >= self.data_limit
        
    @property
    def effective_device_limit(self) -> int:
        """Возвращает эффективный лимит устройств с учётом значения по умолчанию."""
        from ..core.config import settings
        return self.device_limit if self.device_limit is not None else settings.HWID_FALLBACK_DEVICE_LIMIT
