import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, generate_password_reset_token, verify_password_reset_token
from app.models.user import User
from app.schemas.token import TokenPayload, Token, TokenData
from app.schemas.user import UserCreate, UserInDB, User as UserSchema, UserResetPassword, UserUpdatePassword
from app.services.email import EmailService

logger = logging.getLogger(__name__)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Сервис для аутентификации и авторизации пользователей."""
    
    @classmethod
    def create_access_token(
        cls, 
        subject: str, 
        user_id: int,
        is_superuser: bool = False,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Создает JWT токен доступа.
        
        Args:
            subject: Идентификатор пользователя (обычно email)
            user_id: ID пользователя в БД
            is_superuser: Является ли пользователь администратором
            expires_delta: Время жизни токена
            
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
            "exp": expire,
            "sub": str(subject),
            "user_id": user_id,
            "is_superuser": is_superuser,
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @classmethod
    def create_refresh_token(
        cls, 
        subject: str,
        user_id: int,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Создает refresh токен.
        
        Args:
            subject: Идентификатор пользователя (обычно email)
            user_id: ID пользователя в БД
            expires_delta: Время жизни токена
            
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
            "exp": expire,
            "sub": str(subject),
            "user_id": user_id,
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Верифицирует JWT токен и возвращает его полезную нагрузку.
        
        Args:
            token: JWT токен для верификации
            
        Returns:
            Optional[Dict[str, Any]]: Полезная нагрузка токена или None, если токен невалидный
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"Ошибка при верификации токена: {str(e)}")
            return None
    
    @classmethod
    async def authenticate(
        cls, 
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """
        Аутентифицирует пользователя по email и паролю.
        
        Args:
            db: Асинхронная сессия БД
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            Optional[User]: Объект пользователя или None, если аутентификация не удалась
        """
        # Ищем пользователя по email
        user = await User.get_by_email(db, email=email)
        if not user:
            return None
            
        # Проверяем пароль
        if not verify_password(password, user.hashed_password):
            return None
            
        # Обновляем время последнего входа
        user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @classmethod
    async def register_user(
        cls, 
        db: AsyncSession, 
        user_in: UserCreate
    ) -> User:
        """
        Регистрирует нового пользователя.
        
        Args:
            db: Асинхронная сессия БД
            user_in: Данные для регистрации пользователя
            
        Returns:
            User: Созданный пользователь
        """
        # Проверяем, существует ли пользователь с таким email
        existing_user = await User.get_by_email(db, email=user_in.email)
        if existing_user:
            raise ValueError("Пользователь с таким email уже зарегистрирован")
            
        # Создаем нового пользователя
        user_data = user_in.dict(exclude={"password"})
        user_data["hashed_password"] = get_password_hash(user_in.password)
        user = User(**user_data)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @classmethod
    async def create_tokens(
        cls, 
        user: User,
        remember_me: bool = False
    ) -> Dict[str, str]:
        """
        Создает access и refresh токены для пользователя.
        
        Args:
            user: Объект пользователя
            remember_me: Запомнить пользователя на длительный срок
            
        Returns:
            Dict[str, str]: Словарь с access и refresh токенами
        """
        # Определяем время жизни токенов
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        if remember_me:
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            refresh_token_expires = timedelta(hours=12)
        
        # Создаем токены
        access_token = cls.create_access_token(
            subject=user.email,
            user_id=user.id,
            is_superuser=user.is_superuser,
            expires_delta=access_token_expires
        )
        
        refresh_token = cls.create_refresh_token(
            subject=user.email,
            user_id=user.id,
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": (datetime.utcnow() + access_token_expires).isoformat()
        }
    
    @classmethod
    async def refresh_tokens(
        cls, 
        db: AsyncSession, 
        refresh_token: str
    ) -> Dict[str, str]:
        """
        Обновляет access токен с помощью refresh токена.
        
        Args:
            db: Асинхронная сессия БД
            refresh_token: Refresh токен
            
        Returns:
            Dict[str, str]: Новые access и refresh токены
            
        Raises:
            ValueError: Если refresh токен невалидный или пользователь не найден
        """
        # Верифицируем refresh токен
        payload = cls.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Невалидный refresh токен")
            
        # Получаем идентификатор пользователя из токена
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Невалидный формат токена")
            
        # Проверяем, существует ли пользователь
        user = await User.get(db, user_id)
        if not user:
            raise ValueError("Пользователь не найден")
            
        # Создаем новые токены
        return await cls.create_tokens(user)
    
    @classmethod
    async def request_password_reset(
        cls,
        db: AsyncSession,
        email: str
    ) -> bool:
        """
        Запрашивает сброс пароля для пользователя.
        
        Args:
            db: Асинхронная сессия БД
            email: Email пользователя
            
        Returns:
            bool: True, если запрос на сброс пароля обработан
            
        Raises:
            ValueError: Если пользователь с таким email не найден
        """
        # Проверяем, существует ли пользователь с таким email
        user = await User.get_by_email(db, email=email)
        if not user:
            # В продакшене не сообщаем, что пользователь не найден
            if not settings.DEBUG:
                return True
            raise ValueError("Пользователь с таким email не найден")
        
        # Генерируем токен для сброса пароля
        reset_token = generate_password_reset_token(email=email)
        
        # Отправляем письмо с инструкциями
        await EmailService.send_reset_password_email(
            email_to=user.email,
            username=user.username or user.email.split('@')[0],
            token=reset_token
        )
        
        return True
    
    @classmethod
    async def reset_password(
        cls,
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> bool:
        """
        Сбрасывает пароль пользователя с помощью токена.
        
        Args:
            db: Асинхронная сессия БД
            token: Токен для сброса пароля
            new_password: Новый пароль
            
        Returns:
            bool: True, если пароль успешно изменен
            
        Raises:
            ValueError: Если токен невалидный или пользователь не найден
        """
        # Верифицируем токен
        email = verify_password_reset_token(token)
        if not email:
            raise ValueError("Неверный или истекший токен сброса пароля")
        
        # Находим пользователя по email
        user = await User.get_by_email(db, email=email)
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Обновляем пароль
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        # Сбрасываем токены, если есть
        if hasattr(user, 'refresh_token'):
            user.refresh_token = None
        
        await db.commit()
        await db.refresh(user)
        
        return True
    
    @classmethod
    async def send_email_verification(
        cls,
        db: AsyncSession,
        email: str
    ) -> bool:
        """
        Отправляет письмо для подтверждения email.
        
        Args:
            db: Асинхронная сессия БД
            email: Email пользователя
            
        Returns:
            bool: True, если письмо успешно отправлено
            
        Raises:
            ValueError: Если пользователь с таким email не найден или email уже подтвержден
        """
        # Проверяем, существует ли пользователь с таким email
        user = await User.get_by_email(db, email=email)
        if not user:
            if not settings.DEBUG:
                return True
            raise ValueError("Пользователь с таким email не найден")
            
        # Проверяем, не подтвержден ли уже email
        if user.is_verified:
            raise ValueError("Email уже подтвержден")
        
        # Генерируем токен подтверждения email
        from app.core.security import generate_email_verification_token
        token = generate_email_verification_token(email=email)
        
        # Отправляем письмо с подтверждением
        return await EmailService.send_email_verification(
            email_to=user.email,
            username=user.username or user.email.split('@')[0],
            token=token
        )
    
    @classmethod
    async def verify_email(
        cls,
        db: AsyncSession,
        token: str
    ) -> bool:
        """
        Подтверждает email пользователя с помощью токена.
        
        Args:
            db: Асинхронная сессия БД
            token: Токен подтверждения email
            
        Returns:
            bool: True, если email успешно подтвержден
            
        Raises:
            ValueError: Если токен невалидный или пользователь не найден
        """
        from app.core.security import verify_email_verification_token
        
        # Верифицируем токен
        email = verify_email_verification_token(token)
        if not email:
            raise ValueError("Неверный или истекший токен подтверждения email")
        
        # Находим пользователя по email
        user = await User.get_by_email(db, email=email)
        if not user:
            raise ValueError("Пользователь не найден")
            
        # Проверяем, не подтвержден ли уже email
        if user.is_verified:
            return True
            
        # Обновляем статус подтверждения email
        user.is_verified = True
        user.verified_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return True
