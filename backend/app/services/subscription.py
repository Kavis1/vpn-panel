"""
Сервис для управления подписками и тарифами пользователей.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.config import settings
from app.models.subscription import SubscriptionStatus
from app.models.node import Plan

class SubscriptionService:
    """Сервис для управления подписками пользователей."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_subscription_plan(
        self,
        plan_in: schemas.SubscriptionPlanCreate,
        current_user: models.User
    ) -> models.Plan:
        """Создает новый тарифный план."""
        # Проверяем права доступа
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для создания тарифного плана"
            )
        
        # Проверяем, существует ли план с таким именем
        existing_plan = await crud.subscription_plan.get_by_name(self.db, name=plan_in.name)
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Тарифный план с именем '{plan_in.name}' уже существует"
            )
        
        # Создаем тарифный план
        plan = await crud.subscription_plan.create(
            self.db,
            obj_in=plan_in,
            created_by_id=current_user.id
        )
        
        return plan
    
    async def update_subscription_plan(
        self,
        plan_id: int,
        plan_in: schemas.SubscriptionPlanUpdate,
        current_user: models.User
    ) -> models.Plan:
        """Обновляет тарифный план."""
        # Проверяем права доступа
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для обновления тарифного плана"
            )
        
        # Получаем тарифный план
        plan = await crud.subscription_plan.get(self.db, id=plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тарифный план не найден"
            )
        
        # Обновляем тарифный план
        plan = await crud.subscription_plan.update(
            self.db,
            db_obj=plan,
            obj_in=plan_in,
            updated_by_id=current_user.id
        )
        
        return plan
    
    async def delete_subscription_plan(
        self,
        plan_id: int,
        current_user: models.User
    ) -> models.Plan:
        """Удаляет тарифный план."""
        # Проверяем права доступа
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для удаления тарифного плана"
            )
        
        # Проверяем, есть ли активные подписки на этот план
        active_subscriptions = await crud.user_subscription.count_active_by_plan(
            self.db,
            plan_id=plan_id
        )
        
        if active_subscriptions > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно удалить тарифный план с активными подписками"
            )
        
        # Удаляем тарифный план
        plan = await crud.subscription_plan.remove(self.db, id=plan_id)
        
        return plan
    
    async def subscribe_user(
        self,
        user_id: int,
        plan_id: int,
        current_user: models.User
    ) -> models.Subscription:
        """Оформляет подписку пользователя на тарифный план."""
        # Проверяем права доступа
        if not current_user.is_superuser and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для оформления подписки"
            )
        
        # Получаем пользователя и тарифный план
        user = await crud.user.get(self.db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        plan = await crud.subscription_plan.get(self.db, id=plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тарифный план не найден"
            )
        
        # Проверяем, активна ли уже подписка у пользователя
        active_subscription = await crud.user_subscription.get_active_by_user(
            self.db,
            user_id=user_id
        )
        
        if active_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="У пользователя уже есть активная подписка"
            )
        
        # Рассчитываем дату окончания подписки
        now = datetime.utcnow()
        end_date = now + timedelta(days=plan.duration_days)
        
        # Создаем подписку
        subscription_in = schemas.SubscriptionCreate(
            user_id=user_id,
            plan_id=plan_id
        )
        
        subscription = await crud.user_subscription.create(
            self.db,
            obj_in=subscription_in
        )
        
        return subscription
    
    async def update_subscription_status(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
        current_user: models.User
    ) -> models.Subscription:
        """Обновляет статус подписки."""
        # Проверяем права доступа
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для обновления статуса подписки"
            )
        
        # Получаем подписку
        subscription = await crud.user_subscription.get(self.db, id=subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Подписка не найдена"
            )
        
        # Обновляем статус подписки
        subscription_update = schemas.SubscriptionUpdate(
            status=status,
            updated_at=datetime.utcnow()
        )
        
        subscription = await crud.user_subscription.update(
            self.db,
            db_obj=subscription,
            obj_in=subscription_update
        )
        
        return subscription
    
    async def update_used_traffic(
        self,
        user_id: int,
        uploaded: int,
        downloaded: int
    ) -> bool:
        """
        Обновляет использованный трафик для активной подписки пользователя.
        Возвращает True, если лимит трафика не превышен, иначе False.
        """
        # Получаем активную подписку пользователя
        subscription = await crud.user_subscription.get_active_by_user(
            self.db,
            user_id=user_id
        )
        
        if not subscription:
            return False
        
        # Обновляем использованный трафик
        total_used = subscription.used_traffic + uploaded + downloaded
        
        # Проверяем, не превышен ли лимит трафика
        if total_used > subscription.traffic_limit and subscription.traffic_limit > 0:
            # Превышен лимит трафика, отключаем подписку
            subscription_update = schemas.SubscriptionUpdate(
                data_used=total_used,
                is_active=False
            )
            
            await crud.user_subscription.update(
                self.db,
                db_obj=subscription,
                obj_in=subscription_update
            )
            
            return False
        
        # Обновляем использованный трафик
        subscription_update = schemas.SubscriptionUpdate(
            data_used=total_used
        )
        
        await crud.user_subscription.update(
            self.db,
            db_obj=subscription,
            obj_in=subscription_update
        )
        
        return True
    
    async def check_subscription_status(self, user_id: int) -> Dict[str, any]:
        """Проверяет статус подписки пользователя."""
        # Получаем активную подписку пользователя
        subscription = await crud.user_subscription.get_active_by_user(
            self.db,
            user_id=user_id
        )
        
        if not subscription:
            return {
                "has_active_subscription": False,
                "message": "У вас нет активной подписки"
            }
        
        # Проверяем срок действия подписки
        now = datetime.utcnow()
        if now > subscription.end_date:
            # Подписка истекла
            subscription_update = schemas.SubscriptionUpdate(
                is_active=False
            )
            
            await crud.user_subscription.update(
                self.db,
                db_obj=subscription,
                obj_in=subscription_update
            )
            
            return {
                "has_active_subscription": False,
                "message": "Срок действия вашей подписки истек"
            }
        
        # Проверяем лимит трафика
        if subscription.used_traffic >= subscription.traffic_limit > 0:
            # Лимит трафика исчерпан
            subscription_update = schemas.SubscriptionUpdate(
                is_active=False
            )
            
            await crud.user_subscription.update(
                self.db,
                db_obj=subscription,
                obj_in=subscription_update
            )
            
            return {
                "has_active_subscription": False,
                "message": "Лимит трафика исчерпан"
            }
        
        # Подписка активна
        days_left = (subscription.end_date - now).days
        traffic_left = max(0, subscription.traffic_limit - subscription.used_traffic) \
            if subscription.traffic_limit > 0 else float('inf')
        
        return {
            "has_active_subscription": True,
            "subscription_id": subscription.id,
            "plan_name": subscription.plan.name,
            "start_date": subscription.start_date,
            "end_date": subscription.end_date,
            "days_left": days_left,
            "traffic_limit": subscription.traffic_limit,
            "used_traffic": subscription.used_traffic,
            "traffic_left": traffic_left,
            "status": subscription.status
        }
