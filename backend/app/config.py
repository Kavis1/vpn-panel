# Импортируем настройки из нового места для обратной совместимости
from .core.config import Settings, settings

# Экспортируем для обратной совместимости
__all__ = ['Settings', 'settings']