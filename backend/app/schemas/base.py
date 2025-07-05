from datetime import datetime
from typing import Optional, TypeVar, Generic, Type, Any, Dict, List
from pydantic import BaseModel as PydanticBaseModel, Field
from pydantic.generics import GenericModel
from uuid import UUID

# Тип для Generic модели
ModelType = TypeVar("ModelType")

class BaseModel(PydanticBaseModel):
    """Базовая схема для всех моделей."""
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }

class BaseResponse(BaseModel):
    """Базовая схема для ответов API."""
    success: bool = True
    message: Optional[str] = None

class PaginatedResponse(GenericModel, Generic[ModelType]):
    """Схема для постраничного вывода."""
    items: List[ModelType]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        orm_mode = True
