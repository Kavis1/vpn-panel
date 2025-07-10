# Импортируем зависимости, чтобы они были доступны через app.api.deps
from .base import (
    get_db,
    get_current_user,
    get_current_active_user,
    get_current_active_superuser,
    get_pagination_params,
)

__all__ = [
    'get_db',
    'get_current_user',
    'get_current_active_user',
    'get_current_active_superuser',
    'get_pagination_params',
]
