import asyncio
from src.core.database import db_manager
from sqlalchemy import text

async def main():
    try:
        async for session in db_manager.get_session():
            result = await session.execute(text("SELECT 1"))
            print(result.all())
            break
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
