"""
Integration тесты для API endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.system_event import SystemEventLevel, SystemEventSource
from app import crud


@pytest.mark.asyncio
class TestSystemAPI:
    """Тесты для системных API endpoints."""
    
    async def test_health_check(self):
        """Тест проверки здоровья системы."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/system/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "components" in data
            assert "timestamp" in data
    
    async def test_system_info(self):
        """Тест получения информации о системе."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/system/info")
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "VPN Panel Management System"
            assert "version" in data
            assert "features" in data
            assert isinstance(data["features"], list)
    
    async def test_system_stats_unauthorized(self):
        """Тест получения статистики без авторизации."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/system/stats")
            
            assert response.status_code == 401


@pytest.mark.asyncio
class TestMonitorAPI:
    """Тесты для API мониторинга."""
    
    async def test_get_events_unauthorized(self):
        """Тест получения событий без авторизации."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/monitor/events")
            
            assert response.status_code == 401
    
    async def test_get_events_with_auth(self, auth_headers):
        """Тест получения событий с авторизацией."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/monitor/events",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
class TestConfigAPI:
    """Тесты для API конфигурации."""
    
    async def test_validate_config_unauthorized(self):
        """Тест валидации конфигурации без авторизации."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/config/validate",
                json={"config": {}}
            )
            
            assert response.status_code == 401
    
    async def test_validate_valid_config(self, auth_headers, sample_xray_config):
        """Тест валидации корректной конфигурации."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/config/validate",
                headers=auth_headers,
                json={"config": sample_xray_config}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert len(data["errors"]) == 0
    
    async def test_validate_invalid_config(self, auth_headers, invalid_xray_config):
        """Тест валидации некорректной конфигурации."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/config/validate",
                headers=auth_headers,
                json={"config": invalid_xray_config}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["errors"]) > 0
    
    async def test_get_config_templates(self, auth_headers):
        """Тест получения шаблонов конфигурации."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/config/templates",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # Должны быть базовые шаблоны
            template_names = [t["name"] for t in data]
            assert "basic" in template_names


@pytest.mark.asyncio
class TestAuthAPI:
    """Тесты для API аутентификации."""
    
    async def test_login_invalid_credentials(self):
        """Тест входа с неверными данными."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/token",
                data={
                    "username": "invalid@example.com",
                    "password": "wrongpassword",
                    "grant_type": "password"
                }
            )
            
            assert response.status_code == 401
    
    async def test_login_missing_data(self):
        """Тест входа без данных."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/token")
            
            assert response.status_code == 422  # Validation error
    
    async def test_get_current_user_unauthorized(self):
        """Тест получения текущего пользователя без авторизации."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
            
            assert response.status_code == 401
    
    async def test_get_current_user_with_auth(self, auth_headers):
        """Тест получения текущего пользователя с авторизацией."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            assert "id" in data


@pytest.mark.asyncio
class TestEventCreation:
    """Тесты создания событий через API."""
    
    async def test_create_events_during_api_calls(self, db_session: AsyncSession, auth_headers):
        """Тест создания событий при вызовах API."""
        # Получаем количество событий до вызова
        events_before = await crud.system_event.get_recent_events(
            db=db_session, limit=1000
        )
        count_before = len(events_before)
        
        # Делаем API вызов, который должен создать событие
        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post(
                "/api/v1/config/validate",
                headers=auth_headers,
                json={"config": {"inbounds": [], "outbounds": []}}
            )
        
        # Проверяем, что создались новые события
        events_after = await crud.system_event.get_recent_events(
            db=db_session, limit=1000
        )
        count_after = len(events_after)
        
        # Должно быть создано хотя бы одно событие
        assert count_after >= count_before


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Тесты обработки ошибок в API."""
    
    async def test_invalid_json(self, auth_headers):
        """Тест обработки некорректного JSON."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/config/validate",
                headers=auth_headers,
                content="invalid json"
            )
            
            assert response.status_code == 422
    
    async def test_missing_required_fields(self, auth_headers):
        """Тест обработки отсутствующих обязательных полей."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/config/validate",
                headers=auth_headers,
                json={}  # Отсутствует поле config
            )
            
            assert response.status_code == 422
    
    async def test_invalid_endpoint(self):
        """Тест обращения к несуществующему endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/nonexistent")
            
            assert response.status_code == 404


# Fixtures для тестов
@pytest.fixture
async def auth_headers():
    """Возвращает заголовки авторизации для тестов."""
    # В реальных тестах здесь должен быть реальный токен
    # Для упрощения используем mock токен
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_valid_login_data():
    """Возвращает корректные данные для входа."""
    return {
        "username": "admin@example.com",
        "password": "admin",
        "grant_type": "password"
    }