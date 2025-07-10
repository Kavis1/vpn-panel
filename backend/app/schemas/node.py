from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class NodeBase(BaseModel):
    """Базовая схема ноды"""
    name: str
    fqdn: str
    ip_address: str
    api_address: str = "localhost"
    api_port: int = 8080
    api_tag: str = "api"
    is_active: bool = True

class NodeCreate(NodeBase):
    """Схема для создания ноды"""
    pass

class NodeUpdate(BaseModel):
    """Схема для обновления ноды"""
    name: Optional[str] = None
    is_active: Optional[bool] = None

class NodeInDB(NodeBase):
    """Схема ноды в БД"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Node(NodeInDB):
    """Схема ноды для API"""
    pass