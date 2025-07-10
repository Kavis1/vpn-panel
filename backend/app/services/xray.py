"""
Сервис для работы с Xray-core.
Обеспечивает управление конфигурацией, пользователями и сбор статистики.
"""
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import aiohttp
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.user import UserCreate, User
from app.models.node import Node

logger = logging.getLogger(__name__)

class XrayConfig(BaseModel):
    """Модель конфигурации Xray."""
    inbounds: List[Dict]
    outbounds: List[Dict]
    routing: Dict
    stats: Dict = {}
    policy: Dict = {}
    api: Optional[Dict] = None
    log: Optional[Dict] = None
    dns: Optional[Dict] = None

    class Config:
        json_encoders = {
            Path: lambda p: str(p.absolute())
        }

class XrayService:
    """Сервис для работы с Xray-core."""
    
    async def validate_config(self, config: Dict) -> Dict[str, Any]:
        """
        Валидация конфигурации Xray.
        
        Args:
            config: Конфигурация Xray для валидации
            
        Returns:
            Словарь с результатами валидации
        """
        errors = []
        warnings = []
        
        try:
            # Проверяем обязательные поля
            if not isinstance(config, dict):
                errors.append("Конфигурация должна быть объектом JSON")
                return {"is_valid": False, "errors": errors, "warnings": warnings}
            
            # Проверяем inbounds
            if "inbounds" not in config:
                errors.append("Отсутствует секция 'inbounds'")
            elif not isinstance(config["inbounds"], list):
                errors.append("Секция 'inbounds' должна быть массивом")
            else:
                for i, inbound in enumerate(config["inbounds"]):
                    self._validate_inbound(inbound, i, errors, warnings)
            
            # Проверяем outbounds
            if "outbounds" not in config:
                errors.append("Отсутствует секция 'outbounds'")
            elif not isinstance(config["outbounds"], list):
                errors.append("Секция 'outbounds' должна быть массивом")
            else:
                for i, outbound in enumerate(config["outbounds"]):
                    self._validate_outbound(outbound, i, errors, warnings)
            
            # Проверяем routing (опционально)
            if "routing" in config:
                self._validate_routing(config["routing"], errors, warnings)
            
            # Проверяем log (опционально)
            if "log" in config:
                self._validate_log(config["log"], errors, warnings)
            
            # Проверяем dns (опционально)
            if "dns" in config:
                self._validate_dns(config["dns"], errors, warnings)
            
            # Проверяем stats (опционально)
            if "stats" in config:
                self._validate_stats(config["stats"], errors, warnings)
            
            # Проверяем api (опционально)
            if "api" in config:
                self._validate_api(config["api"], errors, warnings)
            
            is_valid = len(errors) == 0
            
            return {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Ошибка валидации конфигурации Xray: {e}")
            return {
                "is_valid": False,
                "errors": [f"Внутренняя ошибка валидации: {str(e)}"],
                "warnings": warnings
            }
    
    def _validate_inbound(self, inbound: Dict, index: int, errors: List[str], warnings: List[str]) -> None:
        """Валидация inbound конфигурации."""
        prefix = f"inbounds[{index}]"
        
        # Проверяем обязательные поля
        if "protocol" not in inbound:
            errors.append(f"{prefix}: отсутствует поле 'protocol'")
        elif inbound["protocol"] not in ["vmess", "vless", "trojan", "shadowsocks", "http", "socks"]:
            errors.append(f"{prefix}: неподдерживаемый протокол '{inbound['protocol']}'")
        
        if "port" not in inbound:
            errors.append(f"{prefix}: отсутствует поле 'port'")
        elif not isinstance(inbound["port"], int) or not (1 <= inbound["port"] <= 65535):
            errors.append(f"{prefix}: некорректный порт '{inbound['port']}'")
        
        # Проверяем settings
        if "settings" not in inbound:
            warnings.append(f"{prefix}: отсутствует секция 'settings'")
        
        # Проверяем streamSettings
        if "streamSettings" in inbound:
            self._validate_stream_settings(inbound["streamSettings"], f"{prefix}.streamSettings", errors, warnings)
    
    def _validate_outbound(self, outbound: Dict, index: int, errors: List[str], warnings: List[str]) -> None:
        """Валидация outbound конфигурации."""
        prefix = f"outbounds[{index}]"
        
        # Проверяем обязательные поля
        if "protocol" not in outbound:
            errors.append(f"{prefix}: отсутствует поле 'protocol'")
        elif outbound["protocol"] not in ["freedom", "blackhole", "dns", "vmess", "vless", "trojan", "shadowsocks"]:
            errors.append(f"{prefix}: неподдерживаемый протокол '{outbound['protocol']}'")
        
        # tag опционален, но если есть, должен быть строкой
        if "tag" in outbound and not isinstance(outbound["tag"], str):
            errors.append(f"{prefix}: поле 'tag' должно быть строкой")
    
    def _validate_stream_settings(self, stream_settings: Dict, prefix: str, errors: List[str], warnings: List[str]) -> None:
        """Валидация streamSettings."""
        if "network" in stream_settings:
            network = stream_settings["network"]
            if network not in ["tcp", "kcp", "ws", "http", "domainsocket", "quic", "grpc"]:
                errors.append(f"{prefix}: неподдерживаемый тип сети '{network}'")
        
        if "security" in stream_settings:
            security = stream_settings["security"]
            if security not in ["none", "tls", "xtls"]:
                errors.append(f"{prefix}: неподдерживаемый тип безопасности '{security}'")
    
    def _validate_routing(self, routing: Dict, errors: List[str], warnings: List[str]) -> None:
        """Валидация routing конфигурации."""
        if "domainStrategy" in routing:
            strategy = routing["domainStrategy"]
            if strategy not in ["AsIs", "UseIP", "UseIPv4", "UseIPv6", "IPIfNonMatch", "IPOnDemand"]:
                errors.append(f"routing: неподдерживаемая стратегия домена '{strategy}'")
        
        if "rules" in routing and not isinstance(routing["rules"], list):
            errors.append("routing: поле 'rules' должно быть массивом")
    
    def _validate_log(self, log: Dict, errors: List[str], warnings: List[str]) -> None:
        """Валидация log конфигурации."""
        if "loglevel" in log:
            level = log["loglevel"]
            if level not in ["debug", "info", "warning", "error", "none"]:
                errors.append(f"log: неподдерживаемый уровень логирования '{level}'")
    
    def _validate_dns(self, dns: Dict, errors: List[str], warnings: List[str]) -> None:
        """Валидация DNS конфигурации."""
        if "servers" in dns and not isinstance(dns["servers"], list):
            errors.append("dns: поле 'servers' должно быть массивом")
    
    def _validate_stats(self, stats: Dict, errors: List[str], warnings: List[str]) -> None:
        """Валидация stats конфигурации."""
        # stats обычно пустой объект, просто проверяем что это объект
        if not isinstance(stats, dict):
            errors.append("stats: должно быть объектом")
    
    def _validate_api(self, api: Dict, errors: List[str], warnings: List[str]) -> None:
        """Валидация API конфигурации."""
        if "tag" in api and not isinstance(api["tag"], str):
            errors.append("api: поле 'tag' должно быть строкой")
        
        if "services" in api and not isinstance(api["services"], list):
            errors.append("api: поле 'services' должно быть массивом")
    
    async def _log_event(
        self,
        level: str,
        message: str,
        source: str = "xray",
        category: str = "config",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логирование событий в системе."""
        try:
            from app import crud
            await crud.system_event.create_event(
                db=self.db,
                level=level,
                message=message,
                source=source,
                category=category,
                details=details
            )
        except Exception as e:
            logger.error(f"Ошибка логирования события: {e}")
    
    """Сервис для управления Xray-core."""
    
    def __init__(self, node: Optional[Node] = None, db: Optional[AsyncSession] = None):
        self.node = node or self._get_local_node()
        self.db = db
        self.config_path = Path(settings.XRAY_CONFIG_DIR) / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_url = f"http://{settings.XRAY_API_ADDRESS}:{settings.XRAY_API_PORT}"
        
    @staticmethod
    def _get_local_node() -> Node:
        """Возвращает локальную ноду из настроек."""
        return Node(
            name="Local Node",
            fqdn=settings.SERVER_HOST,
            ip_address="127.0.0.1",
            api_address=settings.XRAY_API_ADDRESS,
            api_port=settings.XRAY_API_PORT,
            api_tag=settings.XRAY_API_TAG,
            is_active=True
        )
    
    async def start(self) -> bool:
        """Запускает Xray с текущей конфигурацией."""
        try:
            await self._reload_config()
            cmd = [str(settings.XRAY_EXECUTABLE_PATH), "run", "-config", str(self.config_path)]
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return await self.check_status()
        except Exception as e:
            logger.error(f"Failed to start Xray: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """Останавливает Xray."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/stop") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to stop Xray: {str(e)}")
            return False
    
    async def restart(self) -> bool:
        """Перезапускает Xray."""
        if await self.stop():
            return await self.start()
        return False
    
    async def check_status(self) -> bool:
        """Проверяет статус Xray."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/ping") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def add_user(self, user: Union[UserCreate, User], protocol: str = "vless") -> bool:
        """Добавляет пользователя в конфигурацию Xray."""
        try:
            config = await self._load_config()
            
            # Находим соответствующий inbound для протокола
            for inbound in config.inbounds:
                if inbound.get('protocol') == protocol:
                    if 'settings' not in inbound:
                        inbound['settings'] = {}
                    if 'clients' not in inbound['settings']:
                        inbound['settings']['clients'] = []
                    
                    # Добавляем пользователя в конфигурацию
                    user_config = {
                        'id': str(user.uuid),
                        'email': user.email,
                        'level': 0,
                        'alterId': 0
                    }
                    inbound['settings']['clients'].append(user_config)
                    
                    # Сохраняем обновленную конфигурацию
                    await self._save_config(config.dict())
                    await self._reload_config()
                    return True
            
            logger.error(f"Protocol {protocol} not found in Xray configuration")
            return False
            
        except Exception as e:
            logger.error(f"Failed to add user to Xray: {str(e)}")
            return False
    
    async def remove_user(self, user_id: str) -> bool:
        """Удаляет пользователя из конфигурации Xray."""
        try:
            config = await self._load_config()
            user_removed = False
            
            # Ищем и удаляем пользователя из всех inbounds
            for inbound in config.inbounds:
                if 'settings' in inbound and 'clients' in inbound['settings']:
                    original_count = len(inbound['settings']['clients'])
                    inbound['settings']['clients'] = [
                        client for client in inbound['settings']['clients'] 
                        if client.get('id') != user_id
                    ]
                    if len(inbound['settings']['clients']) < original_count:
                        user_removed = True
            
            if user_removed:
                await self._save_config(config.dict())
                await self._reload_config()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove user from Xray: {str(e)}")
            if self.db:
                await self._log_event(
                    level="error",
                    message=f"Ошибка удаления пользователя: {str(e)}",
                    category="user_management",
                    details={"error": str(e), "user_email": user_email}
                )
            return False
    
    async def get_user_stats(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Получает статистику пользователя."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/stats/user/{user_email}") as response:
                    if response.status == 200:
                        stats = await response.json()
                        return {
                            "uplink": stats.get("uplink", 0),
                            "downlink": stats.get("downlink", 0),
                            "total": stats.get("uplink", 0) + stats.get("downlink", 0)
                        }
                    return None
        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователя {user_email}: {str(e)}")
            return None
    
    async def get_system_stats(self) -> Optional[Dict[str, Any]]:
        """Получает общую статистику системы."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/stats/system") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Ошибка получения системной статистики: {str(e)}")
            return None
    
    async def reset_user_stats(self, user_email: str) -> bool:
        """Сбрасывает статистику пользователя."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/stats/user/{user_email}/reset") as response:
                    success = response.status == 200
                    if success and self.db:
                        await self._log_event(
                            level="info",
                            message=f"Статистика пользователя {user_email} сброшена",
                            category="user_management",
                            details={"user_email": user_email}
                        )
                    return success
        except Exception as e:
            logger.error(f"Ошибка сброса статистики пользователя {user_email}: {str(e)}")
            if self.db:
                await self._log_event(
                    level="error",
                    message=f"Ошибка сброса статистики пользователя {user_email}: {str(e)}",
                    category="user_management",
                    details={"error": str(e), "user_email": user_email}
                )
            return False
    
    async def get_stats(self) -> Dict:
        """Возвращает статистику использования Xray."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/stats") as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except Exception as e:
            logger.error(f"Failed to get Xray stats: {str(e)}")
            return {}
    
    async def _load_config(self) -> XrayConfig:
        """Загружает конфигурацию Xray из файла."""
        if not self.config_path.exists():
            return self._get_default_config()
            
        with open(self.config_path, 'r') as f:
            return XrayConfig(**json.load(f))
    
    async def _save_config(self, config: Dict) -> None:
        """Сохраняет конфигурацию Xray в файл."""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    async def _reload_config(self) -> bool:
        """Перезагружает конфигурацию Xray."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/config/reload") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to reload Xray config: {str(e)}")
            return False
    
    def _get_default_config(self) -> XrayConfig:
        """Возвращает конфигурацию Xray по умолчанию."""
        return XrayConfig(
            inbounds=[
                {
                    "port": 443,
                    "protocol": "vless",
                    "settings": {
                        "clients": [],
                        "decryption": "none"
                    },
                    "streamSettings": {
                        "network": "ws",
                        "security": "tls",
                        "tlsSettings": {
                            "certificates": [
                                {
                                    "certificateFile": "certs/fullchain.pem",
                                    "keyFile": "certs/privkey.pem"
                                }
                            ]
                        },
                        "wsSettings": {
                            "path": "/vless"
                        }
                    }
                }
            ],
            outbounds=[
                {
                    "protocol": "freedom",
                    "settings": {}
                },
                {
                    "protocol": "blackhole",
                    "settings": {},
                    "tag": "blocked"
                }
            ],
            routing={
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                        "type": "field",
                        "ip": ["geoip:private"],
                        "outboundTag": "blocked"
                    }
                ]
            },
            stats={},
            policy={
                "levels": {
                    "0": {
                        "handshake": 4,
                        "connIdle": 300,
                        "uplinkOnly": 2,
                        "downlinkOnly": 5
                    }
                }
            },
            api={
                "tag": settings.XRAY_API_TAG,
                "services": ["HandlerService", "LoggerService", "StatsService"]
            },
            log={
                "loglevel": "warning",
                "access": "logs/xray/access.log",
                "error": "logs/xray/error.log"
            }
        )
