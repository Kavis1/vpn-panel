import asyncio
import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.database import get_db, init_db as init_database
from app.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Данные первого суперпользователя
SUPERUSER_DATA = {
    "email": "admin@example.com",
    "username": "admin",
    "password": "admin",
    "full_name": "Admin",
    "is_superuser": True,
    "is_verified": True,
}

async def create_first_superuser(session: AsyncSession, user_data: Dict[str, Any]) -> None:
    """Создает первого суперпользователя, если он еще не существует."""
    # Проверяем, существует ли уже суперпользователь
    existing_user = await session.get(User, user_data["email"])
    if existing_user is not None:
        logger.info("Суперпользователь уже существует")
        return
    
    # Создаем нового суперпользователя
    user_dict = user_data.copy()
    password = user_dict.pop("password")
    user_dict["hashed_password"] = get_password_hash(password)
    
    user = User(**user_dict)
    session.add(user)
    await session.commit()
    
    logger.info("Создан суперпользователь: %s", user.email)

async def init() -> None:
    """Инициализирует базу данных и создает первого суперпользователя."""
    logger.info("Инициализация базы данных...")
    
    # Инициализируем БД (создаем таблицы)
    await init_database()
    
    # Создаем сессию для работы с БД
    async for session in get_db():
        # Создаем первого суперпользователя
        await create_first_superuser(session, SUPERUSER_DATA)
    
    logger.info("Инициализация базы данных завершена")

if __name__ == "__main__":
    # Запускаем асинхронную инициализацию
    asyncio.run(init())
