from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class Node(Base):
    """Модель ноды VPN"""
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    fqdn = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    api_address = Column(String(255), default="localhost")
    api_port = Column(Integer, default=8080)
    api_tag = Column(String(50), default="api")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    traffic_logs = relationship("TrafficLog", back_populates="node")
    config_syncs = relationship("ConfigSync", back_populates="node")

class Plan(Base):
    """Модель плана подписки"""
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    traffic_limit = Column(Integer)  # в ГБ
    device_limit = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    subscriptions = relationship("Subscription", back_populates="plan")

class NodeStatus(Base):
    """Модель статуса ноды"""
    __tablename__ = "node_status"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, nullable=False)
    status = Column(String(50), default="unknown")
    last_check = Column(DateTime(timezone=True), server_default=func.now())
    response_time = Column(Integer)  # в мс
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())