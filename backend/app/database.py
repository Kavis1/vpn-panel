from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from .config import settings

# Определяем, используем ли мы SQLite
IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

# Создаем базовый класс для моделей
Base = declarative_base()

# Настройки пула соединений
POOL_SETTINGS = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "pool_timeout": 30,
}

# Создаем асинхронный движок SQLAlchemy
if IS_SQLITE:
    # Для SQLite используем NullPool, так как он не поддерживает одновременный доступ
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.APP_DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
else:
    # Для PostgreSQL и других СУБД используем настраиваемый пул соединений
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.APP_DEBUG,
        pool_size=POOL_SETTINGS["pool_size"],
        max_overflow=POOL_SETTINGS["max_overflow"],
        pool_recycle=POOL_SETTINGS["pool_recycle"],
        pool_pre_ping=POOL_SETTINGS["pool_pre_ping"],
        pool_timeout=POOL_SETTINGS["pool_timeout"],
    )

# Создаем фабрику сессий с настройками
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Функция для получения сессии БД
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения асинхронной сессии БД.
    Используется в FastAPI Depends().
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

# Функция для создания таблиц в БД
async def init_db():
    """Создает все таблицы в БД."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция для удаления всех таблиц (использовать с осторожностью!)
async def drop_all():
    """Удаляет все таблицы из БД. Только для тестирования!"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Функция для пересоздания БД (использовать с осторожностью!)
async def recreate_db():
    """Пересоздает все таблицы в БД. Только для тестирования!"""
    await drop_all()
    await init_db()
