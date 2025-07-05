from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, JSON, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class XrayConfig(Base):
    """
    Модель для хранения конфигураций Xray
    """
    __tablename__ = "xray_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, index=True, nullable=False, comment="Версия конфигурации")
    description = Column(Text, nullable=True, comment="Описание изменений")
    config = Column(JSON, nullable=False, comment="Конфигурация в формате JSON")
    checksum = Column(String(64), unique=True, index=True, nullable=False, comment="Хеш-сумма конфигурации")
    is_active = Column(Boolean, default=False, index=True, comment="Активна ли конфигурация")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="ID пользователя, создавшего конфигурацию")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="ID пользователя, обновившего конфигурацию")
    
    # Связи
    creator = relationship("User", foreign_keys=[created_by], back_populates="xray_configs_created")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="xray_configs_updated")
    sync_statuses = relationship("ConfigSync", back_populates="config", cascade="all, delete-orphan")


# Pydantic модели для валидации и сериализации
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class XrayConfigBase(BaseModel):
    version: str = Field(..., max_length=50, description="Версия конфигурации")
    description: Optional[str] = Field(None, description="Описание изменений")
    config: Dict[str, Any] = Field(..., description="Конфигурация в формате JSON")

class XrayConfigCreate(XrayConfigBase):
    """Схема для создания конфигурации"""
    @validator('config')
    def validate_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Конфигурация должна быть словарем")
        return v

class XrayConfigUpdate(XrayConfigBase):
    """Схема для обновления конфигурации"""
    version: Optional[str] = Field(None, max_length=50, description="Версия конфигурации")
    description: Optional[str] = Field(None, description="Описание изменений")
    config: Optional[Dict[str, Any]] = Field(None, description="Конфигурация в формате JSON")
    is_active: Optional[bool] = Field(None, description="Активна ли конфигурация")

class XrayConfigInDBBase(XrayConfigBase):
    """Базовая схема для конфигурации в БД"""
    id: int
    checksum: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    updated_by: Optional[int]
    
    class Config:
        orm_mode = True

class XrayConfigInDB(XrayConfigInDBBase):
    """Схема для конфигурации в БД с дополнительными полями"""
    pass

class XrayConfigResponse(XrayConfigInDBBase):
    """Схема для ответа API"""
    pass
