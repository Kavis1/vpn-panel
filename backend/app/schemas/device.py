"""
Pydantic-схемы для управления устройствами пользователей.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

class DeviceBase(BaseModel):
    """Базовая схема устройства."""
    name: str = Field(..., max_length=100, description="Название устройства")
    device_model: Optional[str] = Field(None, max_length=100, description="Модель устройства")
    os_name: Optional[str] = Field(None, max_length=50, description="Название ОС")
    os_version: Optional[str] = Field(None, max_length=50, description="Версия ОС")
    app_version: Optional[str] = Field(None, max_length=50, description="Версия приложения")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP-адрес устройства")
    is_trusted: bool = Field(False, description="Доверенное ли устройство")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")

class DeviceCreate(DeviceBase):
    """Схема для создания устройства."""
    device_id: str = Field(..., max_length=255, description="Уникальный идентификатор устройства")
    vpn_user_id: Optional[int] = Field(None, description="ID VPN-пользователя")

class DeviceUpdate(BaseModel):
    """Схема для обновления устройства."""
    name: Optional[str] = Field(None, max_length=100, description="Новое название устройства")
    is_trusted: Optional[bool] = Field(None, description="Сделать устройство доверенным")
    is_active: Optional[bool] = Field(None, description="Активно ли устройство")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")

class DeviceInDBBase(DeviceBase):
    """Базовая схема устройства в БД."""
    id: int
    device_id: str
    is_active: bool
    last_active: Optional[datetime] = None
    created_at: datetime
    user_id: int
    vpn_user_id: Optional[int] = None
    
    class Config:
        orm_mode = True

class Device(DeviceInDBBase):
    """Схема для возврата данных об устройстве."""
    is_online: bool = False
    
    @validator('is_online', pre=True, always=True)
    def set_is_online(cls, v, values):
        """Вычисляет, активно ли устройство."""
        if 'last_active' not in values or not values['last_active']:
            return False
        return (datetime.utcnow() - values['last_active']).total_seconds() < 300  # 5 минут

class DeviceInDB(DeviceInDBBase):
    """Схема для устройства в БД."""
    pass

class DeviceList(BaseModel):
    """Схема для списка устройств с пагинацией."""
    items: List[Device] = []
    total: int = 0
    page: int = 1
    size: int = 50
    pages: int = 1

class DeviceActivity(BaseModel):
    """Схема для активности устройства."""
    device_id: int
    timestamp: datetime
    action: str
    details: Optional[Dict[str, Any]] = None

class DeviceStats(BaseModel):
    """Схема для статистики по устройствам."""
    total_devices: int = 0
    active_devices: int = 0
    online_devices: int = 0
    trusted_devices: int = 0
    devices_by_os: Dict[str, int] = {}
    devices_by_model: Dict[str, int] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "total_devices": 42,
                "active_devices": 35,
                "online_devices": 12,
                "trusted_devices": 15,
                "devices_by_os": {
                    "Android": 15,
                    "iOS": 12,
                    "Windows": 10,
                    "macOS": 5
                },
                "devices_by_model": {
                    "iPhone 12": 5,
                    "Samsung Galaxy S21": 4,
                    "Google Pixel 5": 3
                }
            }
        }
