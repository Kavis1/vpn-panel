from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

from .base import BaseModel as BaseSchema

# Базовые схемы
class UserBase(BaseSchema):
    """Базовая схема пользователя."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    phone: Optional[str] = None

# Схемы для создания и обновления
class UserCreate(UserBase):
    """Схема для создания пользователя."""
    email: EmailStr
    password: str
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

class UserUpdate(UserBase):
    """Схема для обновления пользователя."""
    password: Optional[str] = None
    
    @validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

# Схемы для ответов API
class UserInDBBase(UserBase):
    """Базовая схема пользователя в БД."""
    id: int
    uuid: UUID
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Дополнительные схемы для различных сценариев
class UserLogin(BaseModel):
    """Схема для входа пользователя."""
    email: EmailStr
    password: str
    remember_me: bool = False

class UserRegister(UserCreate):
    """Схема для регистрации пользователя."""
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v

class UserPasswordReset(BaseModel):
    """Схема для сброса пароля."""
    email: EmailStr

class UserPasswordResetConfirm(BaseModel):
    """Схема для подтверждения сброса пароля."""
    token: str
    new_password: str
    
    @validator('new_password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

class UserPasswordChange(BaseModel):
    """Схема для изменения пароля."""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

# Схемы для ответов API
class User(UserInDBBase):
    """Схема пользователя для ответа API."""
    pass

class UserInDB(UserInDBBase):
    """Схема пользователя в БД."""
    hashed_password: str

# Схемы для списков и пагинации
class UserList(BaseModel):
    """Схема для списка пользователей."""
    items: List[User]
    total: int
    
    class Config:
        from_attributes = True

class UserVerifyEmail(BaseModel):
    """Схема для подтверждения email."""
    token: str

class MessageResponse(BaseModel):
    """Схема для ответа с сообщением."""
    message: str

# Алиасы для обратной совместимости
UserResetPassword = UserPasswordResetConfirm
UserUpdatePassword = UserPasswordChange
