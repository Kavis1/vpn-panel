from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine
import os

from app.api.endpoints.auth import get_current_active_user
from app.models.node import Node

# Создаем синхронную сессию для совместимости
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
if DATABASE_URL.startswith("sqlite+aiosqlite"):
    DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

sync_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
from sqlalchemy.orm import sessionmaker
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

# Заглушка для нод (fallback)
fake_nodes_db = {
    "1": {
        "id": "1",
        "name": "Node 1",
        "address": "192.168.1.100",
        "port": 443,
        "status": "active",
        "location": "US",
        "created_at": "2024-01-01T00:00:00Z"
    },
    "2": {
        "id": "2",
        "name": "Node 2",
        "address": "192.168.1.101",
        "port": 443,
        "status": "inactive",
        "location": "EU",
        "created_at": "2024-01-01T00:00:00Z"
    }
}

@router.get("/", response_model=List[dict])
async def get_nodes(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Получить список всех нод.
    """
    try:
        # Получаем ноды из базы данных
        result = db.execute(select(Node))
        nodes = result.scalars().all()

        nodes_list = []
        for node in nodes:
            nodes_list.append({
                "id": str(node.id),
                "name": node.name,
                "fqdn": node.fqdn,
                "ip_address": node.ip_address,
                "api_address": node.api_address,
                "api_port": node.api_port,
                "api_tag": node.api_tag,
                "is_active": node.is_active,
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "updated_at": node.updated_at.isoformat() if node.updated_at else None
            })
        return nodes_list
    except Exception as e:
        # Если база данных недоступна, возвращаем заглушку
        nodes = []
        for node_id, node_data in fake_nodes_db.items():
            nodes.append(node_data)
        return nodes

@router.get("/{node_id}")
async def get_node_by_id(
    node_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Получить ноду по ID.
    """
    if node_id not in fake_nodes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    return fake_nodes_db[node_id]

@router.post("/")
async def create_node(
    node_data: dict,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Создать новую ноду.
    """
    # Проверяем права администратора
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Простая заглушка для создания ноды
    new_node = {
        "id": str(len(fake_nodes_db) + 1),
        "name": node_data.get("name"),
        "address": node_data.get("address"),
        "port": node_data.get("port", 443),
        "status": "active",
        "location": node_data.get("location", "Unknown"),
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    fake_nodes_db[new_node["id"]] = new_node
    return new_node
