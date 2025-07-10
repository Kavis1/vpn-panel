"""
CRUD операции для модели VPNUser.
"""
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.vpn_user import VPNUser, VPNUserStatus
from app.schemas.user import UserCreate, UserUpdate  # Используем базовые схемы пока
from app.core.security import get_password_hash, verify_password


class CRUDVPNUser(CRUDBase[VPNUser, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[VPNUser]:
        """Получить VPN пользователя по email."""
        result = await db.execute(select(VPNUser).where(VPNUser.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[VPNUser]:
        """Получить VPN пользователя по username."""
        result = await db.execute(select(VPNUser).where(VPNUser.username == username))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, *, user_id: int) -> Optional[VPNUser]:
        """Получить VPN пользователя по user_id."""
        result = await db.execute(select(VPNUser).where(VPNUser.user_id == user_id))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> VPNUser:
        """Создать нового VPN пользователя."""
        db_obj = VPNUser(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            status=VPNUserStatus.ACTIVE,
            is_active=True,
            traffic_limit=0,
            upload_traffic=0,
            download_traffic=0,
            xtls_enabled=False,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[VPNUser]:
        """Аутентификация VPN пользователя."""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def count_by_status(self, db: AsyncSession, status: VPNUserStatus) -> int:
        """Подсчитать количество пользователей по статусу."""
        result = await db.execute(
            select(func.count(VPNUser.id)).where(VPNUser.status == status)
        )
        return result.scalar() or 0

    async def get_active_users(self, db: AsyncSession) -> List[VPNUser]:
        """Получить всех активных пользователей."""
        result = await db.execute(
            select(VPNUser).where(VPNUser.status == VPNUserStatus.ACTIVE)
        )
        return result.scalars().all()

    async def get_traffic_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Получить статистику трафика."""
        result = await db.execute(
            select(
                func.sum(VPNUser.upload_traffic).label('total_upload'),
                func.sum(VPNUser.download_traffic).label('total_download'),
                func.count(VPNUser.id).label('total_users')
            )
        )
        row = result.first()
        return {
            'total_upload': row.total_upload or 0,
            'total_download': row.total_download or 0,
            'total_users': row.total_users or 0
        }

    async def get_recently_active(self, db: AsyncSession, *, limit: int = 10) -> List[VPNUser]:
        """Получить недавно активных пользователей."""
        result = await db.execute(
            select(VPNUser)
            .where(VPNUser.last_active_at.isnot(None))
            .order_by(VPNUser.last_active_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def count(self, db: AsyncSession) -> int:
        """Подсчитать общее количество VPN пользователей."""
        result = await db.execute(select(func.count(VPNUser.id)))
        return result.scalar() or 0


vpn_user = CRUDVPNUser(VPNUser)