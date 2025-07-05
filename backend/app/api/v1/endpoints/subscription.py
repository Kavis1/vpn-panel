"""
API endpoints для управления подписками и тарифными планами.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.models.subscription import SubscriptionStatus
from app.services.subscription import SubscriptionService

router = APIRouter()

# Эндпоинты для управления тарифными планами

@router.post("/plans/", response_model=schemas.SubscriptionPlan)
async def create_subscription_plan(
    plan_in: schemas.SubscriptionPlanCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Создать новый тарифный план.
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.create_subscription_plan(plan_in, current_user)

@router.get("/plans/", response_model=List[schemas.SubscriptionPlan])
async def read_subscription_plans(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить список тарифных планов.
    """
    plans = await crud.subscription_plan.get_multi(db, skip=skip, limit=limit)
    return plans

@router.get("/plans/{plan_id}", response_model=schemas.SubscriptionPlan)
async def read_subscription_plan(
    plan_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить тарифный план по ID.
    """
    plan = await crud.subscription_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тарифный план не найден"
        )
    return plan

@router.put("/plans/{plan_id}", response_model=schemas.SubscriptionPlan)
async def update_subscription_plan(
    plan_id: int,
    plan_in: schemas.SubscriptionPlanUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Обновить тарифный план.
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.update_subscription_plan(plan_id, plan_in, current_user)

@router.delete("/plans/{plan_id}", response_model=schemas.SubscriptionPlan)
async def delete_subscription_plan(
    plan_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Удалить тарифный план.
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.delete_subscription_plan(plan_id, current_user)

# Эндпоинты для управления подписками пользователей

@router.post("/subscribe/", response_model=schemas.UserSubscription)
async def subscribe_user(
    subscription_in: schemas.UserSubscribe,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Оформить подписку на тарифный план.
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.subscribe_user(
        user_id=current_user.id,
        plan_id=subscription_in.plan_id,
        current_user=current_user
    )

@router.get("/me/", response_model=Dict[str, Any])
async def get_my_subscription(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить информацию о текущей подписке.
    """
    subscription_service = SubscriptionService(db)
    return await subscription_service.check_subscription_status(current_user.id)

@router.get("/users/{user_id}", response_model=List[schemas.UserSubscription])
async def get_user_subscriptions(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить список подписок пользователя (только для администраторов).
    """
    # Проверяем, существует ли пользователь
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    subscriptions = await crud.user_subscription.get_multi_by_user(
        db,
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    
    return subscriptions

@router.put("/{subscription_id}/status", response_model=schemas.UserSubscription)
async def update_subscription_status(
    subscription_id: int,
    status_update: Dict[str, str],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Обновить статус подписки (только для администраторов).
    """
    subscription_service = SubscriptionService(db)
    
    try:
        status = SubscriptionStatus(status_update["status"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус подписки. Допустимые значения: {', '.join([s.value for s in SubscriptionStatus])}"
        )
    
    return await subscription_service.update_subscription_status(
        subscription_id=subscription_id,
        status=status,
        current_user=current_user
    )

@router.get("/stats/", response_model=Dict[str, Any])
async def get_subscription_stats(
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить статистику по подпискам (только для администраторов).
    """
    # Общее количество подписок
    total_subscriptions = await crud.user_subscription.count(db)
    
    # Количество активных подписок
    active_subscriptions = await crud.user_subscription.count_by_status(
        db,
        status=SubscriptionStatus.ACTIVE
    )
    
    # Количество приостановленных подписок
    suspended_subscriptions = await crud.user_subscription.count_by_status(
        db,
        status=SubscriptionStatus.SUSPENDED
    )
    
    # Количество истекших подписок
    expired_subscriptions = await crud.user_subscription.count_by_status(
        db,
        status=SubscriptionStatus.EXPIRED
    )
    
    # Самый популярный тарифный план
    popular_plan = await crud.user_subscription.get_most_popular_plan(db)
    
    return {
        "total_subscriptions": total_subscriptions,
        "active_subscriptions": active_subscriptions,
        "suspended_subscriptions": suspended_subscriptions,
        "expired_subscriptions": expired_subscriptions,
        "popular_plan": popular_plan.name if popular_plan else None,
        "timestamp": datetime.utcnow().isoformat()
    }
