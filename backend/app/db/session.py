"""
Сессии базы данных.
"""
from app.database import async_session_factory, get_db

# Алиас для совместимости
get_async_db = get_db

# Экспортируем для обратной совместимости
__all__ = ['async_session_factory', 'get_db', 'get_async_db']