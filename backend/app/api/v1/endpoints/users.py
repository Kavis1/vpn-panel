from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_active_superuser
from app.models.user import User as UserModel
from app.schemas.user import User, UserCreate, UserUpdate, UserRegister, UserList
from app.services.auth import AuthService

router = APIRouter()

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """
    Получение информации о текущем пользователе.
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """
    Обновление информации о текущем пользователе.
    """
    # Обновляем только те поля, которые были переданы
    update_data = user_in.dict(exclude_unset=True)
    
    # Если передан пароль, хешируем его
    if "password" in update_data and update_data["password"]:
        from app.core.security import get_password_hash
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Обновляем пользователя
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
) -> Any:
    """
    Получение списка пользователей (только для администраторов).
    """
    users = await UserModel.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=User)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
) -> Any:
    """
    Создание нового пользователя (только для администраторов).
    """
    # Проверяем, существует ли пользователь с таким email
    user = await UserModel.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже зарегистрирован."
        )
    
    # Создаем пользователя
    user = await UserModel.create(db, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=User)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
) -> Any:
    """
    Получение информации о пользователе по ID (только для администраторов).
    """
    user = await UserModel.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
) -> Any:
    """
    Обновление информации о пользователе (только для администраторов).
    """
    user = await UserModel.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    
    # Обновляем пользователя
    user = await UserModel.update(db, db_obj=user, obj_in=user_in)
    return user

@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
) -> Any:
    """
    Удаление пользователя (только для администраторов).
    """
    user = await UserModel.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    
    # Нельзя удалить самого себя
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить собственный аккаунт"
        )
    
    # Удаляем пользователя
    await UserModel.remove(db, id=user_id)
    return user

@router.post("/{user_id}/deactivate", response_model=User)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
) -> Any:
    """
    Деактивация пользователя (только для администраторов).
    """
    user = await UserModel.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    
    # Нельзя деактивировать самого себя
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Нельзя деактивировать собственный аккаунт"
        )
    
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/{user_id}/activate", response_model=User)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
) -> Any:
    """
    Активация пользователя (только для администраторов).
    """
    user = await UserModel.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    
    return user
