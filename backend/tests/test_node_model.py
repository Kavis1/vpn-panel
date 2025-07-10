"""
Тесты для модели Node.
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from app.models.node import Node, Plan


class TestNodeModel:
    """Тесты для модели Node."""
    
    def test_node_creation(self):
        """Тест создания ноды."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            country_code="RU",
            city="Moscow"
        )
        
        assert node.name == "Test Node"
        assert node.fqdn == "test.example.com"
        assert node.ip_address == "192.168.1.100"
        assert node.country_code == "RU"
        assert node.city == "Moscow"
        assert node.is_active is True  # По умолчанию
        assert node.is_blocked is False  # По умолчанию
    
    def test_api_url_property_with_ssl(self):
        """Тест свойства api_url с SSL."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            api_ssl=True,
            api_port=8443
        )
        
        expected_url = "https://test.example.com:8443"
        assert node.api_url == expected_url
    
    def test_api_url_property_without_ssl(self):
        """Тест свойства api_url без SSL."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            api_ssl=False,
            api_port=8080
        )
        
        expected_url = "http://test.example.com:8080"
        assert node.api_url == expected_url
    
    def test_is_online_property_recent_activity(self):
        """Тест свойства is_online с недавней активностью."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100"
        )
        # Устанавливаем недавнее время последней активности
        node.last_seen = datetime.utcnow() - timedelta(minutes=2)
        
        assert node.is_online is True
    
    def test_is_online_property_old_activity(self):
        """Тест свойства is_online со старой активностью."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100"
        )
        # Устанавливаем старое время последней активности
        node.last_seen = datetime.utcnow() - timedelta(minutes=10)
        
        assert node.is_online is False
    
    def test_is_online_property_no_activity(self):
        """Тест свойства is_online без активности."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100"
        )
        # last_seen не установлен
        
        assert node.is_online is False
    
    def test_get_available_ips_default_subnet(self):
        """Тест получения доступных IP с подсетью по умолчанию."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100"
        )
        
        ips = node.get_available_ips(count=3)
        
        assert len(ips) == 3
        # Проверяем, что IP из подсети 10.8.0.0/24
        for ip in ips:
            assert ip.startswith("10.8.0.")
    
    def test_get_available_ips_custom_subnet(self):
        """Тест получения доступных IP с пользовательской подсетью."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            config={
                "network": {
                    "subnet": "192.168.100.0/24"
                }
            }
        )
        
        ips = node.get_available_ips(count=2)
        
        assert len(ips) == 2
        # Проверяем, что IP из подсети 192.168.100.0/24
        for ip in ips:
            assert ip.startswith("192.168.100.")
            # Проверяем, что это не зарезервированные адреса
            assert not ip.endswith(".0")  # Адрес сети
            assert not ip.endswith(".255")  # Broadcast адрес
            assert not ip.endswith(".1")  # Шлюз
    
    def test_get_available_ips_small_subnet(self):
        """Тест получения доступных IP из маленькой подсети."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            config={
                "network": {
                    "subnet": "192.168.100.0/30"  # Только 4 адреса
                }
            }
        )
        
        # Запрашиваем больше IP, чем доступно
        ips = node.get_available_ips(count=10)
        
        # Должны получить только доступные IP (исключая сеть, broadcast и шлюз)
        assert len(ips) <= 1  # В /30 подсети только 1 хост доступен
    
    def test_get_available_ips_fallback_on_error(self):
        """Тест fallback при ошибке в get_available_ips."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            config={
                "network": {
                    "subnet": "invalid_subnet"  # Некорректная подсеть
                }
            }
        )
        
        ips = node.get_available_ips(count=3)
        
        # Должны получить fallback IP
        assert len(ips) == 3
        for i, ip in enumerate(ips):
            expected_ip = f"10.8.0.{i+10}"
            assert ip == expected_ip
    
    def test_repr_method(self):
        """Тест метода __repr__."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100"
        )
        
        repr_str = repr(node)
        assert "Test Node" in repr_str
        assert "test.example.com" in repr_str


class TestPlanModel:
    """Тесты для модели Plan."""
    
    def test_plan_creation(self):
        """Тест создания тарифного плана."""
        plan = Plan(
            name="Basic Plan",
            description="Базовый тарифный план",
            data_limit=10737418240,  # 10 GB
            duration_days=30,
            max_devices=3,
            price=9.99,
            currency="USD"
        )
        
        assert plan.name == "Basic Plan"
        assert plan.description == "Базовый тарифный план"
        assert plan.data_limit == 10737418240
        assert plan.duration_days == 30
        assert plan.max_devices == 3
        assert plan.price == 9.99
        assert plan.currency == "USD"
        assert plan.is_active is True  # По умолчанию
    
    def test_formatted_price_property(self):
        """Тест свойства formatted_price."""
        plan = Plan(
            name="Premium Plan",
            price=19.99,
            currency="EUR"
        )
        
        assert plan.formatted_price == "19.99 EUR"
    
    def test_formatted_data_limit_gb(self):
        """Тест форматирования лимита данных в ГБ."""
        plan = Plan(
            name="High Volume Plan",
            data_limit=53687091200  # 50 GB
        )
        
        assert plan.formatted_data_limit == "50.0 ГБ"
    
    def test_formatted_data_limit_mb(self):
        """Тест форматирования лимита данных в МБ."""
        plan = Plan(
            name="Small Plan",
            data_limit=524288000  # 500 MB
        )
        
        assert plan.formatted_data_limit == "500.0 МБ"
    
    def test_formatted_data_limit_kb(self):
        """Тест форматирования лимита данных в КБ."""
        plan = Plan(
            name="Tiny Plan",
            data_limit=512000  # 500 KB
        )
        
        assert plan.formatted_data_limit == "500.0 КБ"
    
    def test_formatted_data_limit_unlimited(self):
        """Тест форматирования безлимитного плана."""
        plan = Plan(
            name="Unlimited Plan",
            data_limit=None
        )
        
        assert plan.formatted_data_limit == "Безлимит"
    
    def test_repr_method(self):
        """Тест метода __repr__."""
        plan = Plan(name="Test Plan")
        
        repr_str = repr(plan)
        assert "Test Plan" in repr_str


class TestNodeModelEdgeCases:
    """Тесты для граничных случаев модели Node."""
    
    def test_get_available_ips_zero_count(self):
        """Тест получения 0 IP адресов."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100"
        )
        
        ips = node.get_available_ips(count=0)
        
        assert len(ips) == 0
    
    def test_get_available_ips_no_config(self):
        """Тест получения IP без конфигурации."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            config=None
        )
        
        ips = node.get_available_ips(count=2)
        
        # Должна использоваться подсеть по умолчанию
        assert len(ips) == 2
        for ip in ips:
            assert ip.startswith("10.8.0.")
    
    def test_get_available_ips_empty_config(self):
        """Тест получения IP с пустой конфигурацией."""
        node = Node(
            name="Test Node",
            fqdn="test.example.com",
            ip_address="192.168.1.100",
            config={}
        )
        
        ips = node.get_available_ips(count=2)
        
        # Должна использоваться подсеть по умолчанию
        assert len(ips) == 2
        for ip in ips:
            assert ip.startswith("10.8.0.")