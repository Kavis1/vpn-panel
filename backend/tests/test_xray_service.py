"""
Тесты для XrayService.
"""
import pytest
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from app.services.xray import XrayService


class TestXrayServiceValidation:
    """Тесты для валидации конфигурации Xray."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.xray_service = XrayService()
    
    async def test_validate_valid_config(self):
        """Тест валидации корректной конфигурации."""
        valid_config = {
            "inbounds": [
                {
                    "protocol": "vless",
                    "port": 443,
                    "settings": {
                        "clients": [],
                        "decryption": "none"
                    }
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom",
                    "tag": "direct"
                }
            ],
            "routing": {
                "domainStrategy": "AsIs",
                "rules": []
            }
        }
        
        result = await self.xray_service.validate_config(valid_config)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    async def test_validate_invalid_config_missing_inbounds(self):
        """Тест валидации конфигурации без inbounds."""
        invalid_config = {
            "outbounds": [
                {
                    "protocol": "freedom",
                    "tag": "direct"
                }
            ]
        }
        
        result = await self.xray_service.validate_config(invalid_config)
        
        assert result["is_valid"] is False
        assert "Отсутствует секция 'inbounds'" in result["errors"]
    
    async def test_validate_invalid_config_missing_outbounds(self):
        """Тест валидации конфигурации без outbounds."""
        invalid_config = {
            "inbounds": [
                {
                    "protocol": "vless",
                    "port": 443
                }
            ]
        }
        
        result = await self.xray_service.validate_config(invalid_config)
        
        assert result["is_valid"] is False
        assert "Отсутствует секция 'outbounds'" in result["errors"]
    
    async def test_validate_invalid_protocol(self):
        """Тест валидации с неподдерживаемым протоколом."""
        invalid_config = {
            "inbounds": [
                {
                    "protocol": "invalid_protocol",
                    "port": 443
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom"
                }
            ]
        }
        
        result = await self.xray_service.validate_config(invalid_config)
        
        assert result["is_valid"] is False
        assert any("неподдерживаемый протокол" in error for error in result["errors"])
    
    async def test_validate_invalid_port(self):
        """Тест валидации с некорректным портом."""
        invalid_config = {
            "inbounds": [
                {
                    "protocol": "vless",
                    "port": 99999  # Некорректный порт
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom"
                }
            ]
        }
        
        result = await self.xray_service.validate_config(invalid_config)
        
        assert result["is_valid"] is False
        assert any("некорректный порт" in error for error in result["errors"])
    
    async def test_validate_invalid_routing_strategy(self):
        """Тест валидации с неподдерживаемой стратегией роутинга."""
        invalid_config = {
            "inbounds": [
                {
                    "protocol": "vless",
                    "port": 443
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom"
                }
            ],
            "routing": {
                "domainStrategy": "InvalidStrategy"
            }
        }
        
        result = await self.xray_service.validate_config(invalid_config)
        
        assert result["is_valid"] is False
        assert any("неподдерживаемая стратегия домена" in error for error in result["errors"])
    
    async def test_validate_non_dict_config(self):
        """Тест валидации не-объекта конфигурации."""
        invalid_config = "not a dict"
        
        result = await self.xray_service.validate_config(invalid_config)
        
        assert result["is_valid"] is False
        assert "Конфигурация должна быть объектом JSON" in result["errors"]


class TestXrayServiceMethods:
    """Тесты для методов XrayService."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.xray_service = XrayService()
    
    @patch('aiohttp.ClientSession.get')
    async def test_check_status_online(self, mock_get):
        """Тест проверки статуса - онлайн."""
        # Мокаем успешный ответ
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.xray_service.check_status()
        
        assert result is True
    
    @patch('aiohttp.ClientSession.get')
    async def test_check_status_offline(self, mock_get):
        """Тест проверки статуса - оффлайн."""
        # Мокаем неуспешный ответ
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.xray_service.check_status()
        
        assert result is False
    
    @patch('aiohttp.ClientSession.get')
    async def test_check_status_exception(self, mock_get):
        """Тест проверки статуса - исключение."""
        # Мокаем исключение
        mock_get.side_effect = Exception("Connection error")
        
        result = await self.xray_service.check_status()
        
        assert result is False
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_user_stats_success(self, mock_get):
        """Тест получения статистики пользователя - успех."""
        # Мокаем успешный ответ со статистикой
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "uplink": 1000000,
            "downlink": 5000000
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.xray_service.get_user_stats("test@example.com")
        
        assert result is not None
        assert result["uplink"] == 1000000
        assert result["downlink"] == 5000000
        assert result["total"] == 6000000
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_user_stats_not_found(self, mock_get):
        """Тест получения статистики пользователя - не найден."""
        # Мокаем ответ 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.xray_service.get_user_stats("nonexistent@example.com")
        
        assert result is None
    
    @patch('aiohttp.ClientSession.post')
    async def test_reset_user_stats_success(self, mock_post):
        """Тест сброса статистики пользователя - успех."""
        # Мокаем успешный ответ
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await self.xray_service.reset_user_stats("test@example.com")
        
        assert result is True
    
    @patch('aiohttp.ClientSession.post')
    async def test_reset_user_stats_failure(self, mock_post):
        """Тест сброса статистики пользователя - неудача."""
        # Мокаем неуспешный ответ
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await self.xray_service.reset_user_stats("test@example.com")
        
        assert result is False


class TestXrayServiceValidationHelpers:
    """Тесты для вспомогательных методов валидации."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.xray_service = XrayService()
    
    def test_validate_inbound_valid(self):
        """Тест валидации корректного inbound."""
        inbound = {
            "protocol": "vless",
            "port": 443,
            "settings": {
                "clients": []
            }
        }
        errors = []
        warnings = []
        
        self.xray_service._validate_inbound(inbound, 0, errors, warnings)
        
        assert len(errors) == 0
    
    def test_validate_inbound_missing_protocol(self):
        """Тест валидации inbound без протокола."""
        inbound = {
            "port": 443
        }
        errors = []
        warnings = []
        
        self.xray_service._validate_inbound(inbound, 0, errors, warnings)
        
        assert any("отсутствует поле 'protocol'" in error for error in errors)
    
    def test_validate_outbound_valid(self):
        """Тест валидации корректного outbound."""
        outbound = {
            "protocol": "freedom",
            "tag": "direct"
        }
        errors = []
        warnings = []
        
        self.xray_service._validate_outbound(outbound, 0, errors, warnings)
        
        assert len(errors) == 0
    
    def test_validate_stream_settings_valid(self):
        """Тест валидации корректных streamSettings."""
        stream_settings = {
            "network": "ws",
            "security": "tls"
        }
        errors = []
        warnings = []
        
        self.xray_service._validate_stream_settings(stream_settings, "test", errors, warnings)
        
        assert len(errors) == 0
    
    def test_validate_stream_settings_invalid_network(self):
        """Тест валидации streamSettings с некорректной сетью."""
        stream_settings = {
            "network": "invalid_network"
        }
        errors = []
        warnings = []
        
        self.xray_service._validate_stream_settings(stream_settings, "test", errors, warnings)
        
        assert any("неподдерживаемый тип сети" in error for error in errors)