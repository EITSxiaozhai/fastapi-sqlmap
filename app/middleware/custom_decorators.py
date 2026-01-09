from functools import wraps
from app.database.database import AsyncSessionLocal


def with_async_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with AsyncSessionLocal() as session:
            try:
                return await func(*args, session=session, **kwargs)
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    return wrapper
