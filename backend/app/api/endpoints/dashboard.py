from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
import random

router = APIRouter()

# Заглушка для данных дашборда
async def get_dashboard_stats() -> Dict[str, Any]:
    """Возвращает статистику для дашборда"""
    return {
        "total_users": random.randint(50, 200),
        "active_users": random.randint(10, 150),
        "total_traffic_gb": round(random.uniform(100, 1000), 2),
        "active_nodes": random.randint(1, 5),
        "uptime_days": random.randint(1, 100),
        "recent_activity": [
            {"id": 1, "user": "user1", "action": "connected", "time": "5 minutes ago"},
            {"id": 2, "user": "admin", "action": "updated_settings", "time": "1 hour ago"},
            {"id": 3, "user": "user2", "action": "disconnected", "time": "2 hours ago"},
        ],
        "traffic_data": [
            {"date": "Mon", "gb": random.randint(1, 10)},
            {"date": "Tue", "gb": random.randint(1, 10)},
            {"date": "Wed", "gb": random.randint(1, 10)},
            {"date": "Thu", "gb": random.randint(1, 10)},
            {"date": "Fri", "gb": random.randint(1, 10)},
            {"date": "Sat", "gb": random.randint(1, 10)},
            {"date": "Sun", "gb": random.randint(1, 10)},
        ],
        "node_status": [
            {"id": 1, "name": "Node 1", "status": "online", "load": random.randint(1, 100), "users": random.randint(1, 50)},
            {"id": 2, "name": "Node 2", "status": "online", "load": random.randint(1, 100), "users": random.randint(1, 50)},
            {"id": 3, "name": "Node 3", "status": "offline", "load": 0, "users": 0},
        ]
    }

@router.get("/stats")
async def get_stats():
    """Получить статистику для дашборда"""
    try:
        stats = await get_dashboard_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nodes/status")
async def get_nodes_status():
    """Получить статус нод"""
    try:
        stats = await get_dashboard_stats()
        return {
            "success": True,
            "data": stats["node_status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-activity")
async def get_recent_activity():
    """Получить последние действия"""
    try:
        stats = await get_dashboard_stats()
        return {
            "success": True,
            "data": stats["recent_activity"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
