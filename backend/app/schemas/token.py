from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class Token(BaseModel):
    """Схема для JWT токена."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    refresh_token: Optional[str] = None

class TokenPayload(BaseModel):
    """Схема для данных в JWT токене."""
    sub: Optional[int] = None  # ID пользователя
    email: Optional[str] = None
    is_superuser: bool = False
    exp: Optional[datetime] = None

class TokenData(BaseModel):
    """Данные для создания токена."""
    email: Optional[EmailStr] = None
    scopes: list[str] = []

class RefreshToken(BaseModel):
    """Схема для обновления токена."""
    refresh_token: str

class TokenCreate(BaseModel):
    """Схема для создания токена."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Схема ответа с токеном."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    refresh_token: Optional[str] = None
    user: dict

    class Config:
        orm_mode = True
