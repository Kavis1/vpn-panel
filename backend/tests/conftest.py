"""
Конфигурация для pytest.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.core.config import settings


# Создаем тестовую базу данных в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Создает тестовый движок базы данных."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
    
    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Очищаем после тестов
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Создает фабрику сессий для тестов."""
    async_session_maker = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    yield async_session_maker


@pytest.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Создает сессию базы данных для каждого теста."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_user_data():
    """Возвращает образец данных пользователя для тестов."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }


@pytest.fixture
def sample_node_data():
    """Возвращает образец данных ноды для тестов."""
    return {
        "name": "Test Node",
        "fqdn": "test.example.com",
        "ip_address": "192.168.1.100",
        "country_code": "RU",
        "city": "Moscow",
        "is_active": True,
        "api_port": 8080,
        "api_ssl": False
    }


@pytest.fixture
def sample_plan_data():
    """Возвращает образец данных тарифного плана для тестов."""
    return {
        "name": "Test Plan",
        "description": "Тестовый тарифный план",
        "data_limit": 10737418240,  # 10 GB
        "duration_days": 30,
        "max_devices": 3,
        "price": 9.99,
        "currency": "USD",
        "is_active": True
    }


@pytest.fixture
def sample_xray_config():
    """Возвращает образец конфигурации Xray для тестов."""
    return {
        "log": {
            "loglevel": "warning"
        },
        "inbounds": [
            {
                "protocol": "vless",
                "port": 443,
                "settings": {
                    "clients": [],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "ws",
                    "wsSettings": {
                        "path": "/vless"
                    },
                    "security": "tls"
                }
            }
        ],
        "outbounds": [
            {
                "protocol": "freedom",
                "tag": "direct"
            },
            {
                "protocol": "blackhole",
                "tag": "blocked"
            }
        ],
        "routing": {
            "domainStrategy": "AsIs",
            "rules": [
                {
                    "type": "field",
                    "outboundTag": "blocked",
                    "domain": ["geosite:category-ads-all"]
                }
            ]
        },
        "stats": {},
        "api": {
            "tag": "api",
            "services": ["HandlerService", "LoggerService", "StatsService"]
        }
    }


@pytest.fixture
def invalid_xray_config():
    """Возвращает некорректную конфигурацию Xray для тестов."""
    return {
        "inbounds": [
            {
                "protocol": "invalid_protocol",  # Некорректный протокол
                "port": 99999,  # Некорректный порт
            }
        ],
        # Отсутствует секция outbounds
        "routing": {
            "domainStrategy": "InvalidStrategy"  # Некорректная стратегия
        }
    }


# Маркеры для pytest
def pytest_configure(config):
    """Конфигурация pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )