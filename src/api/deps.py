from typing import AsyncGenerator
from src.core.database import db_manager
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session
