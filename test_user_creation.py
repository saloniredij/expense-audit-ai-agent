import asyncio
from src.core.database import db_manager
from src.core.repository import BaseRepository
from src.models.core import User

async def main():
    async for db in db_manager.get_session():
        import uuid
        user_repo = BaseRepository(User)
        try:
            print("Creating user...")
            obj = await user_repo.create(db=db, obj_in={"email": str(uuid.uuid4())[:8] + "@example.com"})
            print("User created:", obj.id)
            break
        except Exception as e:
            import traceback
            traceback.print_exc()
            break

asyncio.run(main())
