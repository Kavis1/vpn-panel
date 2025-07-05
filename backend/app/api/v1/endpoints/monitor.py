"""
API endpoints для мониторинга и управления состоянием VPN-нод.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.models.node import NodeStatus
from app.services.node_monitor import NodeMonitor

router = APIRouter()

@router.get("/nodes/status", response_model=Dict[int, bool])
async def get_nodes_status(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить статус всех нод (онлайн/оффлайн).
    """
    monitor = NodeMonitor(db)
    return await monitor.check_all_nodes()

@router.get("/nodes/{node_id}/metrics", response_model=Dict[str, Any])
async def get_node_metrics(
    node_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить метрики производительности ноды.
    """
    # Получаем ноду из базы данных
    node = await crud.node.get(db, id=node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Нода не найдена"
        )
    
    # Проверяем права доступа
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра метрик ноды"
        )
    
    monitor = NodeMonitor(db)
    return await monitor.get_node_metrics(node)

@router.get("/nodes/{node_id}/stats", response_model=Dict[str, Any])
async def get_node_stats(
    node_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить статистику использования ноды.
    """
    # Получаем ноду из базы данных
    node = await crud.node.get(db, id=node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Нода не найдена"
        )
    
    monitor = NodeMonitor(db)
    return await monitor.get_node_stats(node)

@router.post("/nodes/{node_id}/sync", response_model=Dict[str, Any])
async def sync_node_config(
    node_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Синхронизировать конфигурацию с нодой.
    """
    # Получаем ноду из базы данных
    node = await crud.node.get(db, id=node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Нода не найдена"
        )
    
    monitor = NodeMonitor(db)
    success = await monitor.sync_node_config(node)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось синхронизировать конфигурацию с нодой"
        )
    
    return {"status": "success", "message": "Конфигурация успешно синхронизирована"}

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Получить статистику для дашборда.
    """
    monitor = NodeMonitor(db)
    
    # Получаем список всех нод
    nodes = await crud.node.get_multi(db, skip=0, limit=100)
    
    # Получаем статус всех нод
    nodes_status = await monitor.check_all_nodes()
    
    # Собираем статистику по нодам
    nodes_stats = []
    total_users = 0
    total_upload = 0
    total_download = 0
    
    for node in nodes:
        is_online = nodes_status.get(node.id, False)
        
        # Получаем статистику ноды
        stats = {
            "id": node.id,
            "name": node.name,
            "fqdn": node.fqdn,
            "ip_address": node.ip_address,
            "status": "online" if is_online else "offline",
            "location": node.location,
            "users_online": 0,
            "upload_speed": 0,
            "download_speed": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0
        }
        
        if is_online:
            try:
                # Получаем метрики ноды
                metrics = await monitor.get_node_metrics(node)
                if metrics and not metrics.get("error"):
                    stats.update({
                        "cpu_usage": metrics.get("cpu_usage", 0),
                        "memory_usage": metrics.get("memory_usage", 0),
                        "disk_usage": metrics.get("disk_usage", 0)
                    })
                
                # Получаем статистику использования
                node_stats = await monitor.get_node_stats(node)
                if node_stats and not node_stats.get("error"):
                    stats.update({
                        "users_online": node_stats.get("users_online", 0),
                        "upload_speed": node_stats.get("upload_speed", 0),
                        "download_speed": node_stats.get("download_speed", 0)
                    })
                    
                    total_users += node_stats.get("users_online", 0)
                    total_upload += node_stats.get("upload_total", 0)
                    total_download += node_stats.get("download_total", 0)
                    
            except Exception as e:
                logger.error(f"Ошибка при получении статистики ноды {node.id}: {str(e)}")
        
        nodes_stats.append(stats)
    
    # Получаем общую статистику по пользователям
    total_active_users = await crud.vpn_user.count_by_status(db, "active")
    total_suspended_users = await crud.vpn_user.count_by_status(db, "suspended")
    
    # Получаем статистику по трафику
    traffic_stats = await crud.vpn_user.get_traffic_stats(db)
    
    # Формируем ответ
    return {
        "summary": {
            "total_nodes": len(nodes),
            "online_nodes": sum(1 for _, status in nodes_status.items() if status),
            "total_users": total_active_users + total_suspended_users,
            "active_users": total_active_users,
            "users_online": total_users,
            "total_upload": traffic_stats["total_upload"],
            "total_download": traffic_stats["total_download"],
            "total_traffic": traffic_stats["total_upload"] + traffic_stats["total_download"]
        },
        "nodes": nodes_stats,
        "recent_events": await _get_recent_events(db)
    }

async def _get_recent_events(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Получить последние события в системе.
    
    Args:
        db: Сессия базы данных
        limit: Максимальное количество событий
        
    Returns:
        Список последних событий
    """
    # Здесь должна быть реализация получения событий из базы данных
    # Временная заглушка
    return [
        {
            "id": 1,
            "timestamp": "2023-01-01T12:00:00Z",
            "level": "info",
            "message": "Система запущена",
            "source": "system"
        }
    ]
