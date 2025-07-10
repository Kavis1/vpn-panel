"""
Модуль для работы с безопасностью: JWT, OAuth2, хеширование паролей.
"""
from datetime import datetime, timedelta
from typing import Optional, Any, Union, Dict, List, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.token import TokenPayload

# Контекст для хеширования паролей
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=settings.SECURITY_BCRYPT_ROUNDS
)

# Схема OAuth2 для аутентификации
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scopes={
        "me": "Read information about the current user.",
        "users:read": "Read users information.",
        "users:write": "Create or update users.",
        "users:delete": "Delete users.",
        "items:read": "Read items.",
        "items:write": "Create or update items.",
        "admin": "Full administrative access.",
    },
    auto_error=False
)

# Алгоритм подписи JWT
ALGORITHM = settings.ALGORITHM

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    scopes: List[str] = None,
    user_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Создает JWT токен доступа.
    
    Args:
        subject: Идентификатор пользователя (обычно user_id)
        expires_delta: Время жизни токена
        scopes: Список разрешений (scopes) для токена
        user_claims: Дополнительные данные пользователя для включения в токен
        
    Returns:
        str: Закодированный JWT токен
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "iss": settings.JWT_TOKEN_ISSUER,
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "scopes": scopes or [],
        "aud": settings.JWT_TOKEN_AUDIENCE
    }
    
    # Добавляем дополнительные данные пользователя, если они есть
    if user_claims:
        to_encode.update({"user": user_claims})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    jti: str = None
) -> str:
    """
    Создает refresh токен.
    
    Args:
        subject: Идентификатор пользователя (обычно user_id)
        expires_delta: Время жизни токена
        jti: Уникальный идентификатор токена (JWT ID)
        
    Returns:
        str: Закодированный JWT refresh токен
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "iss": settings.JWT_TOKEN_ISSUER,
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "aud": settings.JWT_TOKEN_AUDIENCE
    }
    
    # Добавляем JWT ID, если указан
    if jti:
        to_encode["jti"] = jti
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли пароль хешу.
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль
        
    Returns:
        bool: True если пароль верный, иначе False
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля с использованием bcrypt.
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        str: Хешированный пароль
        
    Raises:
        ValueError: Если пароль пустой или None
    """
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу.
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из БД
        
    Returns:
        bool: True если пароль верный, иначе False
    """
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def generate_password_reset_token(email: str) -> str:
    """
    Генерирует токен для сброса пароля.
    
    Args:
        email: Email пользователя
        
    Returns:
        str: JWT токен для сброса пароля
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    
    to_encode = {
        "exp": expires,
        "iat": now,
        "sub": email,
        "type": "password_reset"
    }
    
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Верифицирует токен сброса пароля.
    
    Args:
        token: JWT токен из ссылки сброса пароля
        
    Returns:
        Optional[str]: Email пользователя, если токен валидный, иначе None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=settings.JWT_TOKEN_AUDIENCE,
            issuer=settings.JWT_TOKEN_ISSUER
        )
        if decoded_token.get("type") != "password_reset":
            return None
        return decoded_token.get("sub")
    except (JWTError, ValidationError):
        return None

async def get_current_user(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    Получает текущего аутентифицированного пользователя по токену.
    
    Args:
        security_scopes: Области доступа, требуемые для эндпоинта
        db: Асинхронная сессия БД
        token: JWT токен из заголовка Authorization
        
    Returns:
        User: Объект пользователя
        
    Raises:
        HTTPException: Если токен невалидный, просрочен или у пользователя нет прав
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодируем токен
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[ALGORITHM],
            audience=settings.JWT_TOKEN_AUDIENCE,
            issuer=settings.JWT_TOKEN_ISSUER
        )
        
        # Проверяем тип токена
        if payload.get("type") != "access":
            raise credentials_exception
            
        # Получаем идентификатор пользователя
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Проверяем scopes, если они требуются
        token_scopes = payload.get("scopes", [])
        if security_scopes.scopes:
            for scope in security_scopes.scopes:
                if scope not in token_scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not enough permissions",
                        headers={"WWW-Authenticate": f"Bearer scope=\"{scope}\""},
                    )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise credentials_exception from e
    
    # Ищем пользователя в БД
    user = await User.get(db, id=user_id)
    if user is None:
        raise credentials_exception
        
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Проверяет, активен ли текущий пользователь.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
        
    Returns:
        User: Объект активного пользователя
        
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
    Проверяет, является ли текущий пользователь суперпользователем.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
        
    Returns:
        User: Объект суперпользователя
        
    Raises:
        HTTPException: Если пользователь не является суперпользователем
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Верифицирует токен сброса пароля.
    
    Args:
        token: JWT токен из ссылки сброса пароля
        
    Returns:
        Optional[str]: Email пользователя, если токен валидный, иначе None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=settings.JWT_TOKEN_AUDIENCE,
            issuer=settings.JWT_TOKEN_ISSUER
        )
        if decoded_token.get("type") != "password_reset":
            return None
        return decoded_token.get("sub")
    except (JWTError, ValidationError):
        return None


def generate_email_verification_token(email: str) -> str:
    """
    Генерирует токен для подтверждения email.
    
    Args:
        email: Email пользователя
        
    Returns:
        str: JWT токен для подтверждения email
    """
    delta = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    
    to_encode = {
        "exp": expires,
        "iat": now,
        "sub": email,
        "type": "email_verification"
    }
    
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Верифицирует токен подтверждения email.
    
    Args:
        token: JWT токен из ссылки подтверждения email
        
    Returns:
        Optional[str]: Email пользователя, если токен валидный, иначе None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=settings.JWT_TOKEN_AUDIENCE,
            issuer=settings.JWT_TOKEN_ISSUER
        )
        if decoded_token.get("type") != "email_verification":
            return None
        return decoded_token.get("sub")
    except (JWTError, ValidationError):
        return None

def verify_node_token(token: str) -> Optional[str]:
    """
    Верифицирует токен ноды.
    
    Args:
        token: JWT токен ноды
        
    Returns:
        Optional[str]: ID ноды, если токен валидный, иначе None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=settings.JWT_TOKEN_AUDIENCE,
            issuer=settings.JWT_TOKEN_ISSUER
        )
        if decoded_token.get("type") != "node_auth":
            return None
        return decoded_token.get("sub")
    except (JWTError, ValidationError):
        return None

def generate_node_token(node_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Генерирует токен для аутентификации ноды.
    
    Args:
        node_id: Идентификатор ноды
        expires_delta: Время жизни токена
        
    Returns:
        str: JWT токен для ноды
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)  # 30 дней по умолчанию
    
    to_encode = {
        "iss": settings.JWT_TOKEN_ISSUER,
        "sub": str(node_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "node_auth",
        "aud": settings.JWT_TOKEN_AUDIENCE
    }
    
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )
