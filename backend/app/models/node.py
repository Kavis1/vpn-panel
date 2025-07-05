from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, INET, CIDR
import uuid
import ipaddress

from ..database import Base

class Node(Base):
    """Модель сервера (ноды) для маршрутизации трафика."""
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Основная информация
    name = Column(String(100), nullable=False, index=True)
    fqdn = Column(String(255), nullable=False, unique=True, index=True)
    ip_address = Column(String(45), nullable=False)  # IPv4 или IPv6
    
    # Статус и доступность
    is_active = Column(Boolean, default=True, index=True)
    is_blocked = Column(Boolean, default=False, index=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    
    # Расположение
    country_code = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Настройки подключения
    ssh_host = Column(String(255), nullable=True)
    ssh_port = Column(Integer, default=22)
    ssh_username = Column(String(100), nullable=True)
    ssh_password = Column(String(255), nullable=True)
    ssh_private_key = Column(String(4096), nullable=True)
    
    # API настройки
    api_port = Column(Integer, default=8080)
    api_ssl = Column(Boolean, default=True)
    api_secret = Column(String(255), nullable=True)
    
    # Лимиты и квоты
    max_users = Column(Integer, nullable=True)  # Максимальное количество пользователей
    user_count = Column(Integer, default=0)     # Текущее количество пользователей
    
    # Мониторинг
    cpu_usage = Column(Float, default=0.0)      # В процентах
    ram_usage = Column(Float, default=0.0)      # В процентах
    disk_usage = Column(Float, default=0.0)     # В процентах
    
    # Дополнительные настройки
    tags = Column(JSON, default=list)           # Теги для группировки и фильтрации
    config = Column(JSON, default=dict)         # Конфигурация ноды
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    traffic_logs = relationship("TrafficLog", back_populates="node")
    
    def __repr__(self):
        return f"<Node {self.name} ({self.fqdn})>"
    
    @property
    def api_url(self) -> str:
        """URL для доступа к API ноды."""
        protocol = "https" if self.api_ssl else "http"
        return f"{protocol}://{self.fqdn}:{self.api_port}"
    
    @property
    def is_online(self) -> bool:
        """Онлайн ли нода (проверка по последнему сеансу связи)."""
        if not self.last_seen:
            return False
        return (datetime.utcnow() - self.last_seen).total_seconds() < 300  # 5 минут
    
    def get_available_ips(self, count: int = 1) -> List[str]:
        """Генерация доступных IP-адресов для пользователей."""
        # TODO: Реализовать логику выделения IP-адресов
        return ["10.0.0.1"]  # Заглушка


class Plan(Base):
    """Модель тарифного плана."""
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Основная информация
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Лимиты
    data_limit = Column(BigInteger, nullable=True)  # В байтах, None = безлимит
    duration_days = Column(Integer, nullable=True)  # Длительность в днях, None = бессрочно
    
    # Ограничения
    max_devices = Column(Integer, default=3)        # Максимальное количество устройств
    speed_limit = Column(Integer, nullable=True)    # В Кбит/с, None = без ограничений
    
    # Цена и валюта
    price = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    
    # Дополнительные настройки
    features = Column(JSON, default=list)           # Список возможностей тарифа
    settings = Column(JSON, default=dict)           # Дополнительные настройки
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def __repr__(self):
        return f"<Plan {self.name}>"
    
    @property
    def formatted_price(self) -> str:
        """Отформатированная цена с валютой."""
        return f"{self.price:.2f} {self.currency}"
    
    @property
    def formatted_data_limit(self) -> str:
        """Отформатированный лимит трафика."""
        if self.data_limit is None:
            return "Безлимит"
        
        # Конвертация байтов в ГБ, МБ, КБ
        gb = self.data_limit / (1024 ** 3)
        if gb >= 1:
            return f"{gb:.1f} ГБ"
        mb = self.data_limit / (1024 ** 2)
        if mb >= 1:
            return f"{mb:.1f} МБ"
        kb = self.data_limit / 1024
        return f"{kb:.1f} КБ"
