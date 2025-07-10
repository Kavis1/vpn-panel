from fastapi import APIRouter

# Импортируем все эндпоинты, чтобы они зарегистрировались
from .endpoints import auth, config, devices, docs, monitor, node, users, vpn_user, xray, xtls
# subscription endpoint temporarily disabled due to schema issues

api_router = APIRouter()

# Включаем роутеры
api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(config.router, prefix="/config", tags=["Конфигурация"])
api_router.include_router(devices.router, prefix="/devices", tags=["Устройства"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["Мониторинг"])
api_router.include_router(node.router, prefix="/nodes", tags=["Ноды"])
# api_router.include_router(subscription.router, prefix="/subscriptions", tags=["Подписки"])  # temporarily disabled
api_router.include_router(vpn_user.router, prefix="/vpn-users", tags=["VPN Пользователи"])
api_router.include_router(xray.router, prefix="/xray", tags=["Xray"])
api_router.include_router(xtls.router, prefix="/xtls", tags=["XTLS"])
api_router.include_router(docs.router, prefix="/system", tags=["Система"])
