from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine
import os

from app.api.endpoints.auth import get_current_active_user
from app.models.subscription import Subscription

# Создаем синхронную сессию для совместимости
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
if DATABASE_URL.startswith("sqlite+aiosqlite"):
    DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

sync_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
from sqlalchemy.orm import sessionmaker
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

# Заглушка для подписок (fallback)
fake_subscriptions_db = {
    "1": {
        "id": "1",
        "user_id": "1",
        "name": "Premium VPN",
        "status": "active",
        "expires_at": "2024-12-31T23:59:59Z",
        "traffic_limit": 100000000000,  # 100GB
        "traffic_used": 25000000000,    # 25GB
        "created_at": "2024-01-01T00:00:00Z"
    },
    "2": {
        "id": "2",
        "user_id": "1",
        "name": "Basic VPN",
        "status": "expired",
        "expires_at": "2024-06-30T23:59:59Z",
        "traffic_limit": 10000000000,   # 10GB
        "traffic_used": 10000000000,    # 10GB
        "created_at": "2024-01-01T00:00:00Z"
    }
}

@router.get("/")
async def get_subscriptions(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Получить список всех подписок.
    """
    try:
        # Получаем подписки из базы данных
        result = db.execute(select(Subscription))
        subscriptions = result.scalars().all()

        subscriptions_list = []
        for subscription in subscriptions:
            subscriptions_list.append({
                "id": str(subscription.id),
                "uuid": str(subscription.uuid),
                "user_id": str(subscription.user_id),
                "plan_id": str(subscription.plan_id),
                "is_active": subscription.is_active,
                "auto_renew": subscription.auto_renew,
                "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
                "data_used": subscription.data_used,
                "settings": subscription.settings,
                "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
                "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
                "is_expired": subscription.is_expired,
                "days_remaining": subscription.days_remaining
            })
        return subscriptions_list
    except Exception as e:
        # Если база данных недоступна, возвращаем заглушку
        subscriptions = []
        for sub_id, sub_data in fake_subscriptions_db.items():
            subscriptions.append(sub_data)
        return subscriptions

@router.get("/{subscription_id}")
async def get_subscription_by_id(
    subscription_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Получить подписку по ID.
    """
    if subscription_id not in fake_subscriptions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return fake_subscriptions_db[subscription_id]

@router.post("/")
async def create_subscription(
    subscription_data: dict,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Создать новую подписку.
    """
    # Проверяем права администратора
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Простая заглушка для создания подписки
    new_subscription = {
        "id": str(len(fake_subscriptions_db) + 1),
        "user_id": subscription_data.get("user_id"),
        "name": subscription_data.get("name"),
        "status": "active",
        "expires_at": subscription_data.get("expires_at", "2024-12-31T23:59:59Z"),
        "traffic_limit": subscription_data.get("traffic_limit", 50000000000),  # 50GB
        "traffic_used": 0,
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    fake_subscriptions_db[new_subscription["id"]] = new_subscription
    return new_subscription
