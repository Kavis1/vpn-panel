"""
Схемы для VPN пользователей.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


class VPNUserBase(BaseModel):
    """Базовая схема VPN пользователя."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    is_active: bool = True
    traffic_limit: int = Field(0, ge=0, description="Лимит трафика в байтах, 0 = безлимит")
    xtls_enabled: bool = False


class VPNUserCreate(VPNUserBase):
    """Схема для создания VPN пользователя."""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v


class VPNUserUpdate(BaseModel):
    """Схема для обновления VPN пользователя."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    traffic_limit: Optional[int] = Field(None, ge=0)
    xtls_enabled: Optional[bool] = None
    status: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v


class VPNUserInDBBase(VPNUserBase):
    """Базовая схема VPN пользователя в БД."""
    id: int
    status: str
    upload_traffic: int
    download_traffic: int
    expires_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VPNUser(VPNUserInDBBase):
    """Схема VPN пользователя для API ответов."""
    pass


class VPNUserInDB(VPNUserInDBBase):
    """Схема VPN пользователя в БД с паролем."""
    hashed_password: str