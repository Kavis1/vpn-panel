# Импортируем все эндпоинты, чтобы они зарегистрировались
from . import auth, users

__all__ = [
    'auth',
    'users',
]
