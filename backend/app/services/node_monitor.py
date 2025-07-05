"""
Сервис для мониторинга и управления состоянием VPN-нод.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.config import settings
from app.models.node import Node, NodeStatus
from app.services.node import NodeService

logger = logging.getLogger(__name__)

class NodeMonitor:
    """Сервис для мониторинга состояния VPN-нод."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.node_service = NodeService(db)
        self._monitoring_task = None
        self._is_running = False
    
    async def start_monitoring(self, interval: int = 300) -> None:
        """
        Запускает периодический мониторинг состояния нод.
        
        Args:
            interval: Интервал проверки состояния нод в секундах (по умолчанию 300)
        """
        if self._is_running:
            logger.warning("Мониторинг уже запущен")
            return
        
        self._is_running = True
        logger.info(f"Запуск мониторинга нод с интервалом {interval} секунд")
        
        async def monitor_loop():
            while self._is_running:
                try:
                    await self.check_all_nodes()
                except Exception as e:
                    logger.error(f"Ошибка при мониторинге нод: {str(e)}")
                
                await asyncio.sleep(interval)
        
        self._monitoring_task = asyncio.create_task(monitor_loop())
    
    async def stop_monitoring(self) -> None:
        """Останавливает мониторинг состояния нод."""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            
        logger.info("Мониторинг нод остановлен")
    
    async def check_all_nodes(self) -> Dict[int, bool]:
        """
        Проверяет состояние всех нод.
        
        Returns:
            Словарь с результатами проверки: {node_id: is_online}
        """
        nodes = await crud.node.get_multi(self.db, skip=0, limit=1000)
        results = {}
        
        for node in nodes:
            try:
                is_online = await self.check_node_health(node)
                results[node.id] = is_online
                
                # Обновляем статус ноды в базе данных
                status = NodeStatus.ONLINE if is_online else NodeStatus.OFFLINE
                await self.node_service.update_node_status(
                    node_id=node.id,
                    status=status,
                    status_message="Проверка состояния"
                )
                
            except Exception as e:
                logger.error(f"Ошибка при проверке ноды {node.name} ({node.fqdn}): {str(e)}")
                results[node.id] = False
        
        return results
    
    async def check_node_health(self, node: models.Node) -> bool:
        """
        Проверяет состояние конкретной ноды.
        
        Args:
            node: Объект ноды
            
        Returns:
            True, если нода доступна, иначе False
        """
        try:
            # Проверяем доступность API ноды
            async with aiohttp.ClientSession() as session:
                # Проверяем базовый эндпоинт /ping
                ping_url = f"{node.api_url}/ping"
                async with session.get(ping_url, timeout=5) as response:
                    if response.status != 200:
                        return False
                    
                    data = await response.json()
                    if data.get("status") != "ok":
                        return False
                
                # Проверяем статус Xray
                xray_status_url = f"{node.api_url}/xray/status"
                async with session.get(xray_status_url, timeout=5) as response:
                    if response.status != 200:
                        return False
                    
                    data = await response.json()
                    if not data.get("is_running", False):
                        return False
                
                # Если все проверки пройдены, нода считается доступной
                return True
                
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            logger.debug(f"Нода {node.name} недоступна: {str(e)}")
            return False
    
    async def get_node_metrics(self, node: models.Node) -> Dict[str, Any]:
        """
        Получает метрики производительности ноды.
        
        Args:
            node: Объект ноды
            
        Returns:
            Словарь с метриками производительности
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Получаем метрики с ноды
                metrics_url = f"{node.api_url}/metrics"
                async with session.get(metrics_url, timeout=10) as response:
                    if response.status != 200:
                        return {"error": f"Ошибка получения метрик: {response.status}"}
                    
                    data = await response.json()
                    return data
                    
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            logger.error(f"Ошибка при получении метрик ноды {node.name}: {str(e)}")
            return {"error": f"Ошибка подключения: {str(e)}"}
    
    async def get_node_stats(self, node: models.Node) -> Dict[str, Any]:
        """
        Получает статистику использования ноды.
        
        Args:
            node: Объект ноды
            
        Returns:
            Словарь со статистикой использования
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Получаем статистику с ноды
                stats_url = f"{node.api_url}/xray/stats"
                async with session.get(stats_url, timeout=10) as response:
                    if response.status != 200:
                        return {"error": f"Ошибка получения статистики: {response.status}"}
                    
                    data = await response.json()
                    
                    # Обрабатываем статистику
                    result = {
                        "users_online": data.get("users_online", 0),
                        "total_users": data.get("total_users", 0),
                        "upload_speed": data.get("upload_speed", 0),
                        "download_speed": data.get("download_speed", 0),
                        "upload_total": data.get("upload_total", 0),
                        "download_total": data.get("download_total", 0),
                        "active_connections": data.get("active_connections", 0),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    return result
                    
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            logger.error(f"Ошибка при получении статистики ноды {node.name}: {str(e)}")
            return {"error": f"Ошибка подключения: {str(e)}"}
    
    async def sync_node_config(self, node: models.Node) -> bool:
        """
        Синхронизирует конфигурацию с нодой.
        
        Args:
            node: Объект ноды
            
        Returns:
            True, если синхронизация прошла успешно, иначе False
        """
        try:
            # Получаем актуальную конфигурацию из базы данных
            config = await self._prepare_node_config(node)
            
            # Отправляем конфигурацию на ноду
            async with aiohttp.ClientSession() as session:
                sync_url = f"{node.api_url}/config/sync"
                async with session.post(
                    sync_url,
                    json=config,
                    headers={"Authorization": f"Bearer {node.auth_token}"},
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"Ошибка синхронизации конфигурации с нодой {node.name}: {error}")
                        return False
                    
                    # Обновляем версию конфигурации ноды
                    data = await response.json()
                    if data.get("status") == "success":
                        await crud.node.update(
                            self.db,
                            db_obj=node,
                            obj_in={"config_version": data.get("config_version")}
                        )
                        return True
                    
                    return False
                    
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            logger.error(f"Ошибка при синхронизации конфигурации с нодой {node.name}: {str(e)}")
            return False
    
    async def _prepare_node_config(self, node: models.Node) -> Dict[str, Any]:
        """
        Подготавливает конфигурацию для отправки на ноду.
        
        Args:
            node: Объект ноды
            
        Returns:
            Словарь с конфигурацией
        """
        # Получаем всех пользователей, которым разрешен доступ к этой ноде
        users = await crud.vpn_user.get_active_users(self.db)
        
        # Формируем конфигурацию Xray
        xray_config = {
            "inbounds": [
                {
                    "port": 443,
                    "protocol": "vless",
                    "settings": {
                        "clients": [
                            {
                                "id": str(user.uuid),
                                "email": user.email,
                                "level": 0,
                                "flow": "xtls-rprx-direct"
                            }
                            for user in users
                        ],
                        "decryption": "none"
                    },
                    "streamSettings": {
                        "network": "ws",
                        "security": "tls",
                        "tlsSettings": {
                            "certificates": [
                                {
                                    "certificateFile": f"/etc/letsencrypt/live/{node.fqdn}/fullchain.pem",
                                    "keyFile": f"/etc/letsencrypt/live/{node.fqdn}/privkey.pem"
                                }
                            ]
                        },
                        "wsSettings": {
                            "path": "/vless"
                        }
                    }
                }
            ],
            "outbounds": [
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
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                        "type": "field",
                        "ip": ["geoip:private"],
                        "outboundTag": "blocked"
                    }
                ]
            }
        }
        
        # Формируем общую конфигурацию ноды
        config = {
            "node_id": node.id,
            "fqdn": node.fqdn,
            "ip_address": node.ip_address,
            "location": node.location,
            "is_active": node.is_active,
            "xray_config": xray_config,
            "config_version": node.config_version + 1,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return config
