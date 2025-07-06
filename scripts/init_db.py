import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))

from app.db.session import async_engine, Base
from app.db.init_db import init_db as db_init_db
from app.core.config import settings

async def init_db():
    # Create all database tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize first admin user
    await db_init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db())
