from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base
from .types import UUID


class SubscriptionStatus(enum.Enum):
    """Статусы подписки."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Subscription(Base):
    """Модель подписки пользователя на тарифный план."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(), default=uuid.uuid4, unique=True, index=True)
    
    # Связи
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    
    # Статус подписки
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)
    
    # Период подписки
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Использованные ресурсы
    data_used = Column(BigInteger, default=0)  # В байтах
    
    # Дополнительные настройки
    settings = Column(JSON, default=dict)  # Дополнительные настройки подписки
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription {self.id} - User {self.user_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Истекла ли подписка."""
        if self.end_date is None:
            return False
        return datetime.utcnow() > self.end_date
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Количество оставшихся дней подписки."""
        if self.end_date is None:
            return None
        remaining = (self.end_date - datetime.utcnow()).days
        return max(0, remaining) if remaining is not None else None
    
    def extend(self, days: int) -> None:
        """Продлить подписку на указанное количество дней."""
        now = datetime.utcnow()
        if self.end_date and self.end_date > now:
            self.end_date += timedelta(days=days)
        else:
            self.end_date = now + timedelta(days=days)
        self.is_active = True
