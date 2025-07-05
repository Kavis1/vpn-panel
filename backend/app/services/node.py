"""
Сервис для управления VPN-нодами.
Обеспечивает регистрацию, аутентификацию и управление нодами.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import aiohttp
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_node_token, verify_node_token
from app.crud import node as crud_node
from app.models.node import Node, NodeStatus
from app.schemas.node import NodeCreate, NodeUpdate, Node as NodeSchema

logger = logging.getLogger(__name__)

class NodeService:
    """Сервис для управления VPN-нодами."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_node(self, node_in: NodeCreate) -> Node:
        """Регистрирует новую ноду в системе."""
        # Проверяем, существует ли уже нода с таким FQDN или IP
        existing_node = await crud_node.get_by_fqdn(self.db, fqdn=node_in.fqdn)
        if existing_node:
            raise HTTPException(
                status_code=400,
                detail=f"Node with FQDN {node_in.fqdn} already exists"
            )
            
        existing_node = await crud_node.get_by_ip(self.db, ip_address=node_in.ip_address)
        if existing_node:
            raise HTTPException(
                status_code=400,
                detail=f"Node with IP {node_in.ip_address} already exists"
            )
        
        # Генерируем токен аутентификации для ноды
        auth_token = generate_node_token(node_in.fqdn)
        
        # Создаем запись о ноде в БД
        db_node = await crud_node.create(
            self.db,
            obj_in=NodeCreate(
                **node_in.dict(),
                auth_token=auth_token,
                status=NodeStatus.ONLINE,
                last_seen=datetime.utcnow()
            )
        )
        
        return db_node
    
    async def authenticate_node(self, fqdn: str, token: str) -> Optional[Node]:
        """Аутентифицирует ноду по токену."""
        # Проверяем валидность токена
        if not verify_node_token(token, fqdn):
            return None
            
        # Находим ноду в БД
        node = await crud_node.get_by_fqdn(self.db, fqdn=fqdn)
        if not node or node.auth_token != token:
            return None
            
        # Обновляем время последней активности
        node.last_seen = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(node)
        
        return node
    
    async def update_node_status(
        self,
        node_id: int,
        status: NodeStatus,
        status_message: str = ""
    ) -> Optional[Node]:
        """Обновляет статус ноды."""
        node = await crud_node.get(self.db, id=node_id)
        if not node:
            return None
            
        node_update = NodeUpdate(
            status=status,
            status_message=status_message,
            last_seen=datetime.utcnow()
        )
        
        return await crud_node.update(self.db, db_obj=node, obj_in=node_update)
    
    async def get_available_nodes(self, protocol: str = None) -> List[Node]:
        """Возвращает список доступных нод."""
        nodes = await crud_node.get_multi(
            self.db,
            filter_params={"status": NodeStatus.ONLINE},
            skip=0,
            limit=100
        )
        
        if protocol:
            nodes = [node for node in nodes if protocol in node.supported_protocols]
            
        return nodes
    
    async def get_node_stats(self, node_id: int) -> Dict:
        """Возвращает статистику по ноде."""
        node = await crud_node.get(self.db, id=node_id)
        if not node:
            return {}
            
        # Здесь можно добавить логику сбора статистики с ноды
        # через API или из БД
        
        return {
            "node_id": node.id,
            "status": node.status,
            "load": 0.0,  # Пример метрики
            "clients_connected": 0,  # Пример метрики
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def sync_node_config(self, node_id: int) -> bool:
        """Синхронизирует конфигурацию с нодой."""
        node = await crud_node.get(self.db, id=node_id)
        if not node:
            return False
            
        try:
            # Здесь будет логика синхронизации конфигурации с нодой
            # через API или SSH
            
            # Пример отправки конфигурации на ноду:
            # config = await self._prepare_node_config(node)
            # success = await self._send_config_to_node(node, config)
            
            # Временно возвращаем True для тестирования
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync config with node {node.fqdn}: {str(e)}")
            return False
    
    async def check_nodes_health(self) -> Dict[int, bool]:
        """Проверяет доступность всех нод."""
        nodes = await crud_node.get_multi(self.db, skip=0, limit=100)
        results = {}
        
        for node in nodes:
            try:
                # Проверяем доступность ноды
                is_online = await self._check_node_health(node)
                
                # Обновляем статус ноды
                status = NodeStatus.ONLINE if is_online else NodeStatus.OFFLINE
                await self.update_node_status(
                    node.id,
                    status=status,
                    status_message="Health check"
                )
                
                results[node.id] = is_online
                
            except Exception as e:
                logger.error(f"Error checking health of node {node.fqdn}: {str(e)}")
                results[node.id] = False
        
        return results
    
    async def _check_node_health(self, node: Node) -> bool:
        """Проверяет доступность ноды."""
        try:
            # Проверяем доступность API ноды
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{node.api_address}:{node.api_port}/ping",
                    timeout=5
                ) as response:
                    return response.status == 200
                    
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False
    
    async def _prepare_node_config(self, node: Node) -> Dict:
        """Подготавливает конфигурацию для отправки на ноду."""
        # Здесь должна быть логика подготовки конфигурации ноды
        # на основе её параметров и глобальных настроек
        
        return {
            "node_id": node.id,
            "fqdn": node.fqdn,
            "ip_address": node.ip_address,
            "api_port": node.api_port,
            "api_secret": node.auth_token,
            "config_version": node.config_version,
            "last_updated": datetime.utcnow().isoformat()
        }
