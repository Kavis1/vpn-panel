"""
Схемы для подписок и тарифных планов.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal


# Схемы для тарифных планов
class PlanBase(BaseModel):
    """Базовая схема тарифного плана."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    duration_days: int = Field(..., gt=0)
    traffic_limit: Optional[int] = Field(None, ge=0, description="Лимит трафика в ГБ, None = безлимит")
    device_limit: int = Field(5, ge=1, description="Максимальное количество устройств")
    is_active: bool = True


class PlanCreate(PlanBase):
    """Схема для создания тарифного плана."""
    pass


class PlanUpdate(BaseModel):
    """Схема для обновления тарифного плана."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    duration_days: Optional[int] = Field(None, gt=0)
    traffic_limit: Optional[int] = Field(None, ge=0)
    device_limit: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class PlanInDB(PlanBase):
    """Схема тарифного плана в БД."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Plan(PlanInDB):
    """Схема тарифного плана для API."""
    pass


# Схемы для подписок
class SubscriptionBase(BaseModel):
    """Базовая схема подписки."""
    user_id: int
    plan_id: int
    is_active: bool = True
    auto_renew: bool = True


class SubscriptionCreate(SubscriptionBase):
    """Схема для создания подписки."""
    pass


class SubscriptionUpdate(BaseModel):
    """Схема для обновления подписки."""
    is_active: Optional[bool] = None
    auto_renew: Optional[bool] = None
    end_date: Optional[datetime] = None
    data_used: Optional[int] = None


class SubscriptionInDB(SubscriptionBase):
    """Схема подписки в БД."""
    id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    data_used: int = 0
    settings: dict = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Subscription(SubscriptionInDB):
    """Схема подписки для API."""
    pass


class SubscriptionWithPlan(Subscription):
    """Схема подписки с информацией о плане."""
    plan: Plan


# Алиасы для совместимости
SubscriptionPlan = Plan
SubscriptionPlanCreate = PlanCreate
SubscriptionPlanUpdate = PlanUpdate
UserSubscription = Subscription
UserSubscriptionCreate = SubscriptionCreate
UserSubscriptionUpdate = SubscriptionUpdate
