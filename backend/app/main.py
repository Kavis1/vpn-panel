from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
import logging
from typing import Optional

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    # Создаем экземпляр приложения
    app = FastAPI(
        title="VPN Panel API",
        description="API для управления VPN-сервисами",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене заменить на конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем статические файлы (для фронтенда)
    static_path = Path(__file__).parent.parent / "static"
    static_path.mkdir(exist_ok=True, parents=True)
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    # Тестовый эндпоинт для проверки работоспособности
    @app.get("/")
    async def root():
        return {
            "message": "Добро пожаловать в VPN Panel API",
            "status": "running",
            "version": "0.1.0"
        }
    
    # Эндпоинт для проверки здоровья
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

# Создаем экземпляр приложения
app = create_application()

def main():
    """Точка входа для запуска приложения через uvicorn"""
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Запуск приложения (для разработки)
if __name__ == "__main__":
    main()
