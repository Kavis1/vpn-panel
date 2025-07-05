"""
Сервис для работы с Xray-core.
Обеспечивает управление конфигурацией, пользователями и сбор статистики.
"""
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

import aiohttp
from pydantic import BaseModel, validator

from app.core.config import settings
from app.models.node import Node
from app.schemas.user import UserCreate, User as UserSchema

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
    """Сервис для управления Xray-core."""
    
    def __init__(self, node: Optional[Node] = None):
        self.node = node or self._get_local_node()
        self.config_path = settings.XRAY_CONFIG_DIR / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_url = f"http://{self.node.api_address}:{self.node.api_port}"
        
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
    
    async def add_user(self, user: Union[UserCreate, UserSchema], protocol: str = "vless") -> bool:
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
                                    "certificateFile": "/etc/letsencrypt/live/example.com/fullchain.pem",
                                    "keyFile": "/etc/letsencrypt/live/example.com/privkey.pem"
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
                "access": "/var/log/xray/access.log",
                "error": "/var/log/xray/error.log"
            }
        )
