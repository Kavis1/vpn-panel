"""
Зависимости для API.

Этот модуль содержит общие зависимости, используемые в API.
"""
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.schemas.token import TokenPayload

# Схема для аутентификации через OAuth2 с Bearer токенами
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# Кэш для хранения активных сессий пользователей
active_sessions = {}

async def get_db() -> Generator:
    """
    Зависимость для получения асинхронной сессии БД.
    
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Зависимость для получения текущего аутентифицированного пользователя.
    
    Args:
        db: Асинхронная сессия БД
        token: JWT токен из заголовка Authorization
        
    Returns:
        User: Объект текущего пользователя
        
    Raises:
        HTTPException: Если токен невалидный или пользователь не найден
    """
    try:
        # Декодируем токен
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Валидируем данные токена
        token_data = TokenPayload(**payload)
        
        # Проверяем тип токена (должен быть access)
        if token_data.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена"
            )
        
        # Получаем пользователя из БД
        user = await User.get(db, id=token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
            
        # Проверяем, активен ли пользователь
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь неактивен"
            )
            
        return user
        
    except (jwt.JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Не удалось проверить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Зависимость для получения текущего активного пользователя.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
        
    Returns:
        User: Объект текущего активного пользователя
        
    Raises:
        HTTPException: Если пользователь неактивен
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен"
        )
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Зависимость для получения текущего суперпользователя.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
        
    Returns:
        User: Объект текущего суперпользователя
        
    Raises:
        HTTPException: Если пользователь не является суперпользователем
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user

def get_pagination_params(
    skip: int = 0,
    limit: int = 100,
) -> dict:
    """
    Зависимость для пагинации.
    
    Args:
        skip: Количество записей, которые нужно пропустить
        limit: Максимальное количество записей для возврата
        
    Returns:
        dict: Параметры пагинации
    """
    return {"skip": skip, "limit": limit}
