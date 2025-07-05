from pydantic import PostgresDsn, validator, AnyHttpUrl, EmailStr, HttpUrl
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Literal
import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Settings(BaseSettings):
    # Настройки приложения
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Генерируем случайный ключ, если не задан
    
    # Настройки CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Настройки базы данных
    DATABASE_URL: str
    SQLALCHEMY_POOL_SIZE: int = 5
    SQLALCHEMY_MAX_OVERFLOW: int = 10
    SQLALCHEMY_ECHO: bool = False
    
    # Настройки JWT
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 дней
    JWT_TOKEN_ISSUER: str = "vpn-panel"
    JWT_TOKEN_AUDIENCE: str = "vpn-panel:auth"
    
    # Настройки первого суперпользователя
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin"
    FIRST_SUPERUSER_USERNAME: str = "admin"
    
    # Настройки Xray
    XRAY_EXECUTABLE_PATH: str = "/usr/local/bin/xray"
    XRAY_CONFIG_DIR: str = "/etc/xray"
    XRAY_API_ADDRESS: str = "localhost"
    XRAY_API_PORT: int = 8080
    XRAY_API_TAG: str = "api"
    
    # Настройки API
    API_V1_STR: str = "/api/v1"
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "VPN Panel"
    SERVER_NAME: str = "vpn-panel"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    
    # Настройки безопасности
    SECURITY_BCRYPT_ROUNDS: int = 12
    SECURITY_PASSWORD_SALT: str = secrets.token_hex(16)
    SECURITY_CONFIRMABLE: bool = False
    SECURITY_RECOVERABLE: bool = True
    SECURITY_TRACKABLE: bool = True
    SECURITY_CHANGEABLE: bool = True
    
    # Настройки сессий
    SESSION_SECRET_KEY: str = secrets.token_hex(32)
    SESSION_LIFETIME: int = 60 * 60 * 24 * 7  # 7 дней в секундах
    
    # Пути
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: Path = BASE_DIR / "static"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Настройки почты (для сброса пароля и уведомлений)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = "noreply@vpn-panel.com"
    EMAILS_FROM_NAME: Optional[str] = "VPN Panel"
    
    # Настройки для фронтенда
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Настройки лимита устройств (HWID)
    HWID_DEVICE_LIMIT_ENABLED: bool = True  # Включить ли проверку лимита устройств
    HWID_FALLBACK_DEVICE_LIMIT: int = 5  # Лимит устройств по умолчанию, если не указан для пользователя
    HWID_MAX_DEVICES_ANNOUNCE: str = "Вы достигли максимального количества разрешенных устройств для вашей подписки."
    HWID_DEVICE_INACTIVITY_DAYS: int = 30  # Через сколько дней неактивное устройство считается устаревшим
    HWID_AUTO_REVOKE_INACTIVE: bool = True  # Автоматически отзывать неактивные устройства
    
    # Валидация CORS
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Валидация URL базы данных
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        # Формируем URL для SQLite по умолчанию
        return f"sqlite+aiosqlite:///{values.get('BASE_DIR')}/sql_app.db"
    
    # Свойства для удобства
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        return self.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    @property
    def ALGORITHM(self) -> str:
        return self.JWT_ALGORITHM
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

# Создаем экземпляр настроек
settings = Settings()

# Создаем необходимые директории
os.makedirs(settings.STATIC_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)

# Алиасы для обратной совместимости
settings.SECRET_KEY = settings.SECRET_KEY or settings.JWT_SECRET_KEY
