# Импортируем сервисы, чтобы они были доступны через app.services
from .auth import AuthService

__all__ = [
    'AuthService',
]
