import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            db_url,
            echo=False,
            future=True,
            pool_size=20,
            max_overflow=10,
        )
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        if self._engine is None:
            raise Exception("DatabaseManager is not initialized")
        await self._engine.dispose()
        
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._sessionmaker is None:
            raise Exception("DatabaseManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

db_manager = DatabaseManager(settings.DATABASE_URL)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session
