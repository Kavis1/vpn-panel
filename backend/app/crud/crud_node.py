from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.node import Node
from app.schemas.node import NodeCreate, NodeUpdate

class CRUDNode(CRUDBase[Node, NodeCreate, NodeUpdate]):
    """CRUD операции для работы с нодами"""
    
    async def get_active_nodes(self, db: AsyncSession) -> List[Node]:
        """Получение активных нод"""
        result = await db.execute(
            select(Node).filter(Node.is_active == True)
        )
        return result.scalars().all()

# Создаем экземпляр CRUD класса
node = CRUDNode(Node)