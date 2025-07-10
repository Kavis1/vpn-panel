from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from app.schemas.token import Token, TokenResponse, RefreshToken
from app.schemas.user import (
    UserLogin, 
    UserRegister, 
    User as UserSchema,
    UserResetPassword,
    UserUpdatePassword,
    UserVerifyEmail,
    MessageResponse
)
from app.services.auth import AuthService

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Вход пользователя в систему.
    
    Принимает email и пароль, возвращает access и refresh токены.
    """
    # Проверяем учетные данные
    user = await AuthService.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токены
    tokens = await AuthService.create_tokens(
        user, 
        remember_me=form_data.scopes and "remember_me" in form_data.scopes
    )
    
    # Возвращаем токены и информацию о пользователе
    return {
        **tokens,
        "user": UserSchema.from_orm(user).dict()
    }

@router.post("/register", response_model=UserSchema)
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Регистрация нового пользователя.
    
    Создает нового пользователя с указанными данными.
    """
    try:
        user = await AuthService.register_user(db, user_in=user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Обновление access токена с помощью refresh токена.
    
    Принимает refresh токен и возвращает новую пару access и refresh токенов.
    """
    try:
        # Обновляем токены
        tokens = await AuthService.refresh_tokens(
            db, refresh_token=refresh_data.refresh_token
        )
        
        # Получаем информацию о пользователе из refresh токена
        payload = AuthService.verify_token(refresh_data.refresh_token)
        if not payload or "user_id" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный refresh токен"
            )
        
        # Получаем пользователя
        user = await User.get(db, payload["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Возвращаем токены и информацию о пользователе
        return {
            **tokens,
            "user": UserSchema.from_orm(user).dict()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/test-token", response_model=UserSchema)
async def test_token(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Тестовый эндпоинт для проверки аутентификации.
    
    Возвращает информацию о текущем аутентифицированном пользователе.
    """
    return current_user

@router.post("/password-recovery/{email}", response_model=MessageResponse)
async def recover_password(
    email: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Запрос на восстановление пароля.
    
    Отправляет письмо с инструкциями по сбросу пароля на указанный email.
    """
    try:
        await AuthService.request_password_reset(db, email=email)
        return {"message": "Если аккаунт с таким email существует, на него отправлено письмо с инструкциями по сбросу пароля"}
    except Exception as e:
        # В продакшене не сообщаем об ошибках
        if not settings.DEBUG:
            return {"message": "Если аккаунт с таким email существует, на него отправлено письмо с инструкциями по сбросу пароля"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/reset-password/", response_model=MessageResponse)
async def reset_password(
    reset_data: UserResetPassword,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Сброс пароля с помощью токена.
    
    Устанавливает новый пароль для пользователя, если токен валидный.
    """
    try:
        await AuthService.reset_password(
            db, 
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        return {"message": "Пароль успешно изменен"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при сбросе пароля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при сбросе пароля"
        )

@router.post("/send-verification-email", response_model=MessageResponse)
async def send_verification_email(
    email: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Отправляет письмо для подтверждения email.
    
    Args:
        email: Email для отправки письма с подтверждением
        
    Returns:
        dict: Сообщение об успешной отправке
    """
    try:
        await AuthService.send_email_verification(db, email=email)
        return {"message": "Письмо с подтверждением отправлено на указанный email"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке письма с подтверждением: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при отправке письма с подтверждением"
        )

@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verify_data: UserVerifyEmail,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Подтверждает email пользователя с помощью токена.
    
    Args:
        token: Токен подтверждения email
        
    Returns:
        dict: Сообщение об успешном подтверждении
    """
    try:
        await AuthService.verify_email(db, token=verify_data.token)
        return {"message": "Email успешно подтвержден"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при подтверждении email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при подтверждении email"
        )


