import asyncio
from src.core.database import db_manager
from src.core.repository import BaseRepository
from src.api.routes.users import create_user
from src.api import schemas
from src.models.core import User

async def main():
    try:
        async for db in db_manager.get_session():
            print("Session acquired")
            user_in = schemas.UserCreate(email="test@example.com")
            user = await create_user(db=db, user_in=user_in)
            print("Successfully created:", user.id)
            break
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
