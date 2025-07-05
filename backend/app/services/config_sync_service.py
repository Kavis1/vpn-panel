"""
Сервис для синхронизации конфигурации между нодами.
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.config import settings
from app.crud.crud_config import config as crud_config
from app.models.config_sync import ConfigSync, SyncStatus
from app.models.config_version import ConfigVersion
from app.models.node import Node, NodeStatus
from app.schemas.config import ConfigDeployResponse, ConfigSyncStatus, NodeSyncStatus

logger = logging.getLogger(__name__)

class ConfigSyncService:
    """Сервис для синхронизации конфигурации между нодами."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._sync_lock = asyncio.Lock()
        self._active_syncs: Dict[int, asyncio.Task] = {}
    
    async def deploy_config(
        self,
        config_version: Union[str, int, ConfigVersion],
        nodes: Optional[List[Union[int, Node]]] = None,
        force: bool = False,
        restart_services: bool = True,
        current_user: Optional[models.User] = None
    ) -> ConfigDeployResponse:
        """
        Развернуть конфигурацию на указанных нодах.
        
        Args:
            config_version: Версия конфигурации (ID, версия или объект ConfigVersion)
            nodes: Список нод (ID или объекты Node). Если None, развертываем на всех активных нодах
            force: Принудительное развертывание, даже если версия совпадает
            restart_services: Перезапускать ли сервисы после развертывания
            current_user: Пользователь, инициировавший развертывание
            
        Returns:
            Ответ с информацией о задаче развертывания
        """
        # Получаем объект конфигурации
        db_config = await self._get_config_version(config_version)
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Конфигурация {config_version} не найдена"
            )
        
        # Получаем список нод для развертывания
        db_nodes = await self._get_nodes_to_sync(nodes)
        if not db_nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет доступных нод для развертывания"
            )
        
        # Создаем задачи синхронизации для каждой ноды
        sync_tasks = []
        for node in db_nodes:
            task = asyncio.create_task(
                self._sync_config_to_node(
                    config=db_config,
                    node=node,
                    force=force,
                    restart_services=restart_services,
                    user_id=current_user.id if current_user else None
                )
            )
            sync_tasks.append(task)
        
        # Запускаем все задачи асинхронно
        await asyncio.gather(*sync_tasks, return_exceptions=True)
        
        # Получаем сводную информацию о синхронизации
        summary = await crud_config.get_config_sync_summary(self.db, config_id=db_config.id)
        
        return ConfigDeployResponse(
            job_id=f"deploy_{db_config.id}_{int(datetime.utcnow().timestamp())}",
            status=summary["sync_status"],
            message=f"Развертывание конфигурации {db_config.version} запущено на {len(db_nodes)} нодах",
            started_at=datetime.utcnow()
        )
    
    async def sync_all_nodes(
        self,
        config_version: Optional[Union[str, int, ConfigVersion]] = None,
        force: bool = False,
        restart_services: bool = True,
        current_user: Optional[models.User] = None
    ) -> ConfigDeployResponse:
        """
        Синхронизировать конфигурацию на всех нодах.
        
        Args:
            config_version: Версия конфигурации (ID, версия или объект ConfigVersion).
                          Если не указана, используется активная конфигурация.
            force: Принудительная синхронизация, даже если версия совпадает
            restart_services: Перезапускать ли сервисы после синхронизации
            current_user: Пользователь, инициировавший синхронизацию
            
        Returns:
            Ответ с информацией о задаче синхронизации
        """
        # Если версия конфигурации не указана, используем активную
        if config_version is None:
            db_config = await crud_config.get_active_config(self.db)
            if not db_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Активная конфигурация не найдена"
                )
        else:
            db_config = await self._get_config_version(config_version)
            if not db_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Конфигурация {config_version} не найдена"
                )
        
        # Получаем список всех активных нод
        db_nodes = await self._get_nodes_to_sync()
        if not db_nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет доступных нод для синхронизации"
            )
        
        # Создаем задачи синхронизации для каждой ноды
        sync_tasks = []
        for node in db_nodes:
            task = asyncio.create_task(
                self._sync_config_to_node(
                    config=db_config,
                    node=node,
                    force=force,
                    restart_services=restart_services,
                    user_id=current_user.id if current_user else None
                )
            )
            sync_tasks.append(task)
        
        # Запускаем все задачи асинхронно
        await asyncio.gather(*sync_tasks, return_exceptions=True)
        
        # Получаем сводную информацию о синхронизации
        summary = await crud_config.get_config_sync_summary(self.db, config_id=db_config.id)
        
        return ConfigDeployResponse(
            job_id=f"sync_all_{db_config.id}_{int(datetime.utcnow().timestamp())}",
            status=summary["sync_status"],
            message=f"Синхронизация конфигурации {db_config.version} запущена на {len(db_nodes)} нодах",
            started_at=datetime.utcnow()
        )
    
    async def get_sync_status(
        self, config_version: Union[str, int, ConfigVersion], node_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить статус синхронизации конфигурации.
        
        Args:
            config_version: Версия конфигурации (ID, версия или объект ConfigVersion)
            node_id: Опциональный ID ноды для фильтрации
            
        Returns:
            Список статусов синхронизации
        """
        db_config = await self._get_config_version(config_version)
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Конфигурация {config_version} не найдена"
            )
        
        # Получаем статусы синхронизации
        sync_statuses = await crud_config.get_sync_status(
            self.db, config_id=db_config.id, node_id=node_id
        )
        
        # Преобразуем в формат ответа API
        result = []
        for status in sync_statuses:
            result.append({
                "node_id": status.node_id,
                "node_name": status.node.name if status.node else None,
                "status": status.status,
                "last_sync": status.last_sync,
                "last_attempt": status.last_attempt,
                "error_message": status.error_message,
                "retry_count": status.retry_count,
                "is_online": status.node.is_online if status.node else False,
                "node_status": status.node.status if status.node else None
            })
        
        return result
    
    async def get_config_sync_summary(
        self, config_version: Union[str, int, ConfigVersion]
    ) -> Dict[str, Any]:
        """
        Получить сводную информацию о синхронизации конфигурации.
        
        Args:
            config_version: Версия конфигурации (ID, версия или объект ConfigVersion)
            
        Returns:
            Словарь с информацией о синхронизации
        """
        db_config = await self._get_config_version(config_version)
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Конфигурация {config_version} не найдена"
            )
        
        return await crud_config.get_config_sync_summary(self.db, config_id=db_config.id)
    
    async def _sync_config_to_node(
        self,
        config: ConfigVersion,
        node: Node,
        force: bool = False,
        restart_services: bool = True,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Синхронизировать конфигурацию с нодой.
        
        Args:
            config: Объект конфигурации
            node: Объект ноды
            force: Принудительная синхронизация, даже если версия совпадает
            restart_services: Перезапускать ли сервисы после синхронизации
            user_id: ID пользователя, инициировавшего синхронизацию
            
        Returns:
            True, если синхронизация прошла успешно, иначе False
        """
        # Создаем или получаем запись о синхронизации
        sync = await self._get_or_create_sync(config.id, node.id)
        
        try:
            # Обновляем статус на "в процессе"
            await crud_config.update_sync_status(
                self.db,
                sync_id=sync.id,
                status=SyncStatus.IN_PROGRESS,
                error_message=None
            )
            
            # Проверяем, нужно ли обновлять конфигурацию
            if not force and sync.status == SyncStatus.COMPLETED:
                logger.info(
                    f"Конфигурация {config.version} уже синхронизирована с нодой {node.name} "
                    f"(ID: {node.id}), пропускаем"
                )
                return True
            
            # Получаем URL API ноды
            node_api_url = node.api_url.rstrip('/')
            sync_url = f"{node_api_url}/api/v1/config/sync"
            
            # Подготавливаем данные для отправки
            payload = {
                "version": config.version,
                "config": config.config,
                "checksum": config.checksum,
                "restart_services": restart_services,
                "force": force
            }
            
            # Отправляем запрос на синхронизацию
            headers = {
                "Authorization": f"Bearer {node.auth_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    sync_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Ошибка при синхронизации с нодой {node.name}: {error_text}"
                        )
                    
                    result = await response.json()
                    if not result.get("success", False):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=result.get("message", "Неизвестная ошибка при синхронизации")
                        )
            
            # Обновляем статус на "завершено"
            await crud_config.update_sync_status(
                self.db,
                sync_id=sync.id,
                status=SyncStatus.COMPLETED,
                error_message=None
            )
            
            logger.info(
                f"Конфигурация {config.version} успешно синхронизирована с нодой {node.name} "
                f"(ID: {node.id})"
            )
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Ошибка при синхронизации конфигурации {config.version} с нодой {node.name} "
                f"(ID: {node.id}): {error_msg}",
                exc_info=True
            )
            
            # Обновляем статус на "ошибка"
            await crud_config.update_sync_status(
                self.db,
                sync_id=sync.id,
                status=SyncStatus.FAILED,
                error_message=error_msg,
                increment_retry=True
            )
            
            return False
    
    async def _get_or_create_sync(
        self, config_id: int, node_id: int
    ) -> ConfigSync:
        """
        Получить или создать запись о синхронизации.
        
        Args:
            config_id: ID конфигурации
            node_id: ID ноды
            
        Returns:
            Объект ConfigSync
        """
        # Пытаемся найти существующую запись
        sync_statuses = await crud_config.get_sync_status(
            self.db, config_id=config_id, node_id=node_id
        )
        
        if sync_statuses:
            return sync_statuses[0]
        
        # Если запись не найдена, создаем новую
        return await crud_config.create_sync_status(
            self.db,
            config_id=config_id,
            node_id=node_id,
            status=SyncStatus.PENDING
        )
    
    async def _get_config_version(
        self, config_version: Union[str, int, ConfigVersion]
    ) -> Optional[ConfigVersion]:
        """
        Получить объект конфигурации по ID, версии или объекту.
        
        Args:
            config_version: ID, версия или объект ConfigVersion
            
        Returns:
            Объект ConfigVersion или None, если не найден
        """
        if isinstance(config_version, ConfigVersion):
            return config_version
        
        if isinstance(config_version, int) or (isinstance(config_version, str) and config_version.isdigit()):
            return await crud_config.get(self.db, id=int(config_version))
        
        if isinstance(config_version, str):
            return await crud_config.get_by_version(self.db, version=config_version)
        
        return None
    
    async def _get_nodes_to_sync(
        self, nodes: Optional[List[Union[int, Node]]] = None
    ) -> List[Node]:
        """
        Получить список нод для синхронизации.
        
        Args:
            nodes: Список нод (ID или объекты Node). Если None, возвращаются все активные ноды.
            
        Returns:
            Список объектов Node
        """
        if nodes is None:
            # Возвращаем все активные ноды
            result = await self.db.execute(
                select(Node)
                .filter(Node.is_active.is_(True))
                .order_by(Node.priority.asc(), Node.id.asc())
            )
            return result.scalars().all()
        
        # Преобразуем список ID/объектов в список объектов Node
        db_nodes = []
        for node in nodes:
            if isinstance(node, Node):
                db_nodes.append(node)
            elif isinstance(node, int):
                db_node = await self.db.get(Node, node)
                if db_node and db_node.is_active:
                    db_nodes.append(db_node)
        
        return db_nodes
