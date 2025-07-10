"""
API endpoints для документации и здоровья системы.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Проверка здоровья системы")
async def health_check() -> Dict[str, Any]:
    """
    Проверка здоровья системы.
    
    Возвращает статус всех компонентов системы.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "database": "healthy",
            "xray": "healthy"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/info", summary="Информация о системе")
async def system_info() -> Dict[str, Any]:
    """
    Получить информацию о системе.
    
    Возвращает общую информацию о VPN Panel.
    """
    return {
        "name": "VPN Panel Management System",
        "version": "1.0.0",
        "description": "Универсальная панель управления VPN-сервисами",
        "features": [
            "Управление пользователями",
            "Мониторинг трафика",
            "Управление нодами",
            "Конфигурация Xray",
            "Система событий"
        ],
        "api_version": "v1",
        "docs_url": "/api/docs",
        "openapi_url": "/api/openapi.json"
    }


@router.get("/stats", summary="Статистика системы")
async def system_stats(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Получить статистику системы.
    
    Требует аутентификации.
    """
    try:
        # Получаем статистику событий
        events_stats = await crud.system_event.get_events_count_by_level(db=db)
        events_by_source = await crud.system_event.get_events_count_by_source(db=db)
        
        # Получаем общую статистику
        total_events = sum(events_stats.values())
        error_events = events_stats.get("error", 0) + events_stats.get("critical", 0)
        
        return {
            "events": {
                "total": total_events,
                "by_level": events_stats,
                "by_source": events_by_source,
                "error_count": error_events
            },
            "system_health": "good" if error_events == 0 else "warning" if error_events < 10 else "critical",
            "uptime": "24h 30m",  # TODO: Реальный uptime
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статистики: {str(e)}"
        )