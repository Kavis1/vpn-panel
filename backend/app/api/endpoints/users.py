from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine
from pydantic import BaseModel
import uuid
import bcrypt
import os

from app.api.endpoints.auth import get_user, fake_users_db, get_current_active_user
from app.models.user import User

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

# Схемы для создания пользователя
class CreateUserRequest(BaseModel):
    email: str
    username: str = None
    password: str
    full_name: str = None
    phone: str = None
    telegram_id: str = None
    is_superuser: bool = False
    is_verified: bool = False
    data_limit: int = None
    device_limit: int = None
    email_notifications: bool = True
    telegram_notifications: bool = False

@router.get("/", response_model=List[dict])
async def get_users(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Получить список всех пользователей.
    """
    # Получаем пользователей из базы данных
    try:
        result = db.execute(select(User))
        users = result.scalars().all()

        users_list = []
        for user in users:
            users_list.append({
                "id": str(user.id),
                "uuid": str(user.uuid),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "data_limit": user.data_limit,
                "data_used": user.data_used,
                "device_limit": user.device_limit,
                "expire_date": user.expire_date.isoformat() if user.expire_date else None,
                "email_notifications": user.email_notifications,
                "telegram_notifications": user.telegram_notifications,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        return users_list
    except Exception as e:
        # Если база данных недоступна, возвращаем данные из fake_users_db
        users = []
        for username, user_data in fake_users_db.items():
            users.append({
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "is_admin": user_data["is_admin"],
                "disabled": user_data["disabled"]
            })
        return users

@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Получить пользователя по ID.
    """
    try:
        # Пытаемся найти пользователя в базе данных
        user = db.execute(select(User).where(User.id == int(user_id))).scalar_one_or_none()

        if user:
            return {
                "id": str(user.id),
                "uuid": str(user.uuid),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "data_limit": user.data_limit,
                "data_used": user.data_used,
                "device_limit": user.device_limit,
                "expire_date": user.expire_date.isoformat() if user.expire_date else None,
                "email_notifications": user.email_notifications,
                "telegram_notifications": user.telegram_notifications,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
    except (ValueError, Exception):
        # Если не удалось найти в БД, ищем в fake_users_db
        for username, user_data in fake_users_db.items():
            if user_data["id"] == user_id:
                return {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "full_name": user_data["full_name"],
                    "is_admin": user_data["is_admin"],
                    "disabled": user_data["disabled"]
                }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.post("/")
async def create_user(
    user_data: CreateUserRequest,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Создать нового пользователя.
    """
    # Проверяем права администратора
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    try:
        # Проверяем, что пользователь с таким email не существует
        existing_user = db.execute(select(User).where(User.email == user_data.email)).scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Хешируем пароль
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Создаем нового пользователя
        new_user = User(
            uuid=uuid.uuid4(),
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            telegram_id=user_data.telegram_id,
            is_superuser=user_data.is_superuser,
            is_verified=user_data.is_verified,
            data_limit=user_data.data_limit,
            device_limit=user_data.device_limit,
            email_notifications=user_data.email_notifications,
            telegram_notifications=user_data.telegram_notifications
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "id": str(new_user.id),
            "uuid": str(new_user.uuid),
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "is_active": new_user.is_active,
            "is_superuser": new_user.is_superuser,
            "is_verified": new_user.is_verified,
            "phone": new_user.phone,
            "telegram_id": new_user.telegram_id,
            "data_limit": new_user.data_limit,
            "data_used": new_user.data_used,
            "device_limit": new_user.device_limit,
            "expire_date": new_user.expire_date.isoformat() if new_user.expire_date else None,
            "email_notifications": new_user.email_notifications,
            "telegram_notifications": new_user.telegram_notifications,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
            "updated_at": new_user.updated_at.isoformat() if new_user.updated_at else None,
            "last_login": new_user.last_login.isoformat() if new_user.last_login else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )



@router.get("/me")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получить профиль текущего пользователя.
    """
    return current_user
