"""
Сервис для управления пользователями VPN.
Обеспечивает создание, обновление и удаление пользователей,
а также управление их настройками доступа.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.security import get_password_hash, verify_password
from app.models.vpn_user import VPNUserStatus

class VPNUserService:
    """Сервис для управления пользователями VPN."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(
        self,
        user_in: schemas.VPNUserCreate,
        current_user: models.User
    ) -> models.VPNUser:
        """
        Создать нового пользователя VPN.
        """
        # Проверяем, существует ли пользователь с таким email
        existing_user = await crud.vpn_user.get_by_email(self.db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже зарегистрирован"
            )
        
        # Проверяем, существует ли пользователь с таким именем
        existing_username = await crud.vpn_user.get_by_username(self.db, username=user_in.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже существует"
            )
        
        # Хешируем пароль
        hashed_password = get_password_hash(user_in.password)
        
        # Создаем пользователя
        user_data = user_in.dict(exclude={"password"})
        user_data["hashed_password"] = hashed_password
        user_data["created_by_id"] = current_user.id
        
        # Устанавливаем срок действия аккаунта, если указан
        if user_in.expires_in_days:
            user_data["expires_at"] = datetime.utcnow() + timedelta(days=user_in.expires_in_days)
        
        user = await crud.vpn_user.create(self.db, obj_in=user_data)
        return user
    
    async def update_user(
        self,
        user_id: int,
        user_in: schemas.VPNUserUpdate,
        current_user: models.User
    ) -> models.VPNUser:
        """
        Обновить данные пользователя VPN.
        """
        # Получаем пользователя
        user = await crud.vpn_user.get(self.db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Проверяем права доступа
        if not current_user.is_superuser and user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для обновления этого пользователя"
            )
        
        # Обновляем данные пользователя
        update_data = user_in.dict(exclude_unset=True)
        
        # Если обновляется пароль, хешируем его
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Обновляем срок действия аккаунта, если указан
        if "expires_in_days" in update_data and update_data["expires_in_days"] is not None:
            if update_data["expires_in_days"] == 0:
                # Бессрочный доступ
                update_data["expires_at"] = None
            else:
                update_data["expires_at"] = datetime.utcnow() + timedelta(days=update_data["expires_in_days"])
            update_data.pop("expires_in_days")
        
        user = await crud.vpn_user.update(
            self.db,
            db_obj=user,
            obj_in=update_data,
            updated_by_id=current_user.id
        )
        
        return user
    
    async def delete_user(
        self,
        user_id: int,
        current_user: models.User
    ) -> models.VPNUser:
        """
        Удалить пользователя VPN.
        """
        # Проверяем права доступа
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для удаления пользователей"
            )
        
        # Получаем пользователя
        user = await crud.vpn_user.get(self.db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Удаляем пользователя
        user = await crud.vpn_user.remove(self.db, id=user_id)
        return user
    
    async def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[models.VPNUser]:
        """
        Аутентификация пользователя VPN.
        """
        user = await crud.vpn_user.authenticate(
            self.db,
            username=username,
            password=password
        )
        
        if not user:
            return None
        
        # Проверяем, не истек ли срок действия аккаунта
        if user.expires_at and user.expires_at < datetime.utcnow():
            # Обновляем статус на "истекший"
            await crud.vpn_user.update(
                self.db,
                db_obj=user,
                obj_in={"status": VPNUserStatus.EXPIRED}
            )
            return None
        
        # Проверяем, активен ли пользователь
        if user.status != VPNUserStatus.ACTIVE:
            return None
        
        return user
    
    async def update_status(
        self,
        user_id: int,
        status: VPNUserStatus,
        current_user: models.User
    ) -> models.VPNUser:
        """
        Обновить статус пользователя VPN.
        """
        # Проверяем права доступа
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для обновления статуса пользователя"
            )
        
        # Получаем пользователя
        user = await crud.vpn_user.get(self.db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Обновляем статус
        user = await crud.vpn_user.update(
            self.db,
            db_obj=user,
            obj_in={"status": status},
            updated_by_id=current_user.id
        )
        
        return user
    
    async def update_traffic_usage(
        self,
        user_id: int,
        upload: int,
        download: int
    ) -> bool:
        """
        Обновить статистику использования трафика пользователем.
        Возвращает True, если лимит трафика не превышен, иначе False.
        """
        # Получаем пользователя
        user = await crud.vpn_user.get(self.db, id=user_id)
        if not user:
            return False
        
        # Обновляем статистику трафика
        total_upload = user.upload_traffic + upload
        total_download = user.download_traffic + download
        total_traffic = total_upload + total_download
        
        # Проверяем, не превышен ли лимит трафика
        if user.traffic_limit > 0 and total_traffic >= user.traffic_limit:
            # Лимит трафика превышен, отключаем пользователя
            await crud.vpn_user.update(
                self.db,
                db_obj=user,
                obj_in={
                    "status": VPNUserStatus.SUSPENDED,
                    "upload_traffic": total_upload,
                    "download_traffic": total_download
                }
            )
            return False
        
        # Обновляем статистику
        await crud.vpn_user.update(
            self.db,
            db_obj=user,
            obj_in={
                "upload_traffic": total_upload,
                "download_traffic": total_download
            }
        )
        
        return True
    
    async def reset_traffic(
        self,
        user_id: int,
        current_user: models.User
    ) -> models.VPNUser:
        """
        Сбросить статистику использования трафика пользователя.
        """
        # Проверяем права доступа
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для сброса статистики трафика"
            )
        
        # Получаем пользователя
        user = await crud.vpn_user.get(self.db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Сбрасываем статистику
        user = await crud.vpn_user.update(
            self.db,
            db_obj=user,
            obj_in={
                "upload_traffic": 0,
                "download_traffic": 0,
                "last_active_at": datetime.utcnow()
            },
            updated_by_id=current_user.id
        )
        
        return user
    
    async def get_user_stats(self, user_id: int) -> Dict[str, any]:
        """
        Получить статистику пользователя.
        """
        user = await crud.vpn_user.get(self.db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Проверяем, не истек ли срок действия аккаунта
        is_expired = user.expires_at and user.expires_at < datetime.utcnow()
        if is_expired and user.status != VPNUserStatus.EXPIRED:
            # Обновляем статус на "истекший"
            user = await crud.vpn_user.update(
                self.db,
                db_obj=user,
                obj_in={"status": VPNUserStatus.EXPIRED}
            )
        
        # Проверяем, не превышен ли лимит трафика
        is_traffic_exceeded = (
            user.traffic_limit > 0 and 
            (user.upload_traffic + user.download_traffic) >= user.traffic_limit
        )
        
        if is_traffic_exceeded and user.status == VPNUserStatus.ACTIVE:
            # Превышен лимит трафика, отключаем пользователя
            user = await crud.vpn_user.update(
                self.db,
                db_obj=user,
                obj_in={"status": VPNUserStatus.SUSPENDED}
            )
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "status": user.status,
            "is_active": user.status == VPNUserStatus.ACTIVE,
            "is_expired": is_expired,
            "is_traffic_exceeded": is_traffic_exceeded,
            "traffic_limit": user.traffic_limit,
            "upload_traffic": user.upload_traffic,
            "download_traffic": user.download_traffic,
            "total_traffic": user.upload_traffic + user.download_traffic,
            "traffic_left": max(0, user.traffic_limit - (user.upload_traffic + user.download_traffic)) 
                           if user.traffic_limit > 0 else float('inf'),
            "created_at": user.created_at,
            "expires_at": user.expires_at,
            "last_active_at": user.last_active_at
        }
