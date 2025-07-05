from fastapi import APIRouter

# Импортируем все эндпоинты, чтобы они зарегистрировались
from .endpoints import auth, users

api_router = APIRouter()

# Включаем роутеры
api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
