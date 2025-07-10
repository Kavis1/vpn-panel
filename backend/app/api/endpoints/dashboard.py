from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ...database import get_db
from ...models.user import User
from ...models.vpn_user import VPNUser, VPNUserStatus
from ...models.node import Node
from ...models.system_event import SystemEvent
from ...models.traffic import TrafficLog

router = APIRouter()

async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
    """Возвращает реальную статистику для дашборда из базы данных"""

    # Общее количество пользователей
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    # Активные пользователи (активные VPN пользователи)
    active_users_result = await db.execute(
        select(func.count(VPNUser.id)).where(VPNUser.status == VPNUserStatus.ACTIVE)
    )
    active_users = active_users_result.scalar() or 0

    # Общий трафик за последний месяц (в GB)
    month_ago = datetime.utcnow() - timedelta(days=30)
    traffic_result = await db.execute(
        select(func.sum(TrafficLog.download + TrafficLog.upload)).where(
            TrafficLog.created_at >= month_ago
        )
    )
    total_traffic_bytes = traffic_result.scalar() or 0
    total_traffic_gb = round(total_traffic_bytes / (1024**3), 2)

    # Количество нод
    total_nodes_result = await db.execute(select(func.count(Node.id)))
    total_nodes = total_nodes_result.scalar() or 0

    active_nodes_result = await db.execute(
        select(func.count(Node.id)).where(Node.is_active == True)
    )
    active_nodes = active_nodes_result.scalar() or 0

    # Время работы системы (дни с первого события)
    first_event_result = await db.execute(
        select(SystemEvent).order_by(SystemEvent.created_at).limit(1)
    )
    first_event = first_event_result.scalar_one_or_none()
    uptime_days = 0
    if first_event:
        uptime_days = (datetime.utcnow() - first_event.created_at).days

    # Последние действия из системных событий
    recent_activities = []
    recent_events_result = await db.execute(
        select(SystemEvent).order_by(desc(SystemEvent.created_at)).limit(10)
    )
    recent_events = recent_events_result.scalars().all()

    for event in recent_events:
        time_diff = datetime.utcnow() - event.created_at
        if time_diff.days > 0:
            time_str = f"{time_diff.days} дн. назад"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} ч. назад"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} мин. назад"
        else:
            time_str = "только что"

        # Определяем статус по типу события
        status = 'info'
        if 'error' in event.event_type.lower() or 'fail' in event.event_type.lower():
            status = 'error'
        elif 'connect' in event.event_type.lower() or 'create' in event.event_type.lower():
            status = 'success'

        recent_activities.append({
            "id": event.id,
            "user": event.user_email or "system",
            "action": event.description or event.event_type,
            "time": time_str,
            "status": status
        })

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_traffic_gb": total_traffic_gb,
        "active_nodes": active_nodes,
        "total_nodes": total_nodes,
        "uptime_days": uptime_days,
        "recent_activities": recent_activities
    }

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Получить реальную статистику для дашборда"""
    try:
        stats = await get_dashboard_stats(db)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nodes/status")
async def get_nodes_status(db: AsyncSession = Depends(get_db)):
    """Получить реальный статус нод"""
    try:
        nodes_result = await db.execute(select(Node))
        nodes = nodes_result.scalars().all()
        node_status = []

        for node in nodes:
            # Подсчитываем пользователей на ноде
            users_count_result = await db.execute(
                select(func.count(VPNUser.id)).where(
                    VPNUser.node_id == node.id,
                    VPNUser.status == VPNUserStatus.ACTIVE
                )
            )
            users_count = users_count_result.scalar() or 0

            node_status.append({
                "id": node.id,
                "name": node.name,
                "address": node.address,
                "status": "online" if node.is_active else "offline",
                "users": users_count,
                "load": 0  # TODO: реализовать подсчет нагрузки
            })

        return {
            "success": True,
            "data": node_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-activity")
async def get_recent_activity(db: AsyncSession = Depends(get_db)):
    """Получить последние действия из системных событий"""
    try:
        stats = await get_dashboard_stats(db)
        return {
            "success": True,
            "data": stats["recent_activities"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
