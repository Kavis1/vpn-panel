from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, and_
from sqlalchemy.dialects.postgresql import UUID, INET
import uuid
import ipaddress

from ..database import Base

class TrafficLog(Base):
    """Модель для логирования трафика пользователей."""
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Связи
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True, index=True)
    
    # Информация о подключении
    remote_ip = Column(INET, nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_id = Column(String(100), nullable=True, index=True)
    
    # Статистика трафика
    upload = Column(BigInteger, default=0)    # Исходящий трафик в байтах
    download = Column(BigInteger, default=0)  # Входящий трафик в байтах
    
    # Временные метки
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Дополнительная информация
    protocol = Column(String(50), nullable=True)  # Протокол (vmess, vless и т.д.)
    metadata_ = Column("metadata", JSON, default=dict)  # Дополнительные метаданные
    
    # Связи
    user = relationship("User", back_populates="traffic_logs")
    node = relationship("Node", back_populates="traffic_logs")
    
    def __repr__(self):
        return f"<TrafficLog User:{self.user_id} Node:{self.node_id} {self.upload}↑ {self.download}↓>"
    
    @property
    def total_traffic(self) -> int:
        """Общий объем трафика в байтах."""
        return self.upload + self.download
    
    @property
    def formatted_total_traffic(self) -> str:
        """Отформатированный общий объем трафика."""
        return self.format_bytes(self.total_traffic)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Длительность сессии."""
        if not self.started_at or not self.ended_at:
            return None
        return self.ended_at - self.started_at
    
    @property
    def is_active(self) -> bool:
        """Активна ли сессия."""
        return self.ended_at is None
    
    @staticmethod
    def format_bytes(size: int) -> str:
        """Форматирует размер в байтах в читаемый вид."""
        if not size:
            return "0 Б"
        
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ПБ"


class TrafficLimit(Base):
    """Модель для хранения лимитов трафика по периодам."""
    __tablename__ = "traffic_limits"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Связи
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Период
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Лимиты
    data_limit = Column(BigInteger, nullable=True)  # В байтах, None = безлимит
    data_used = Column(BigInteger, default=0)       # Использованный трафик в байтах
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<TrafficLimit User:{self.user_id} {self.period_type} {self.period_start.date()}>"
    
    @property
    def data_remaining(self) -> Optional[int]:
        """Оставшийся трафик в байтах."""
        if self.data_limit is None:
            return None
        return max(0, self.data_limit - self.data_used)
    
    @property
    def is_exceeded(self) -> bool:
        """Превышен ли лимит трафика."""
        if self.data_limit is None:
            return False
        return self.data_used >= self.data_limit
