from fastapi import APIRouter
from sqlalchemy import text
from app.database.database import engine

router = APIRouter(
    prefix="/db",
    tags=["Database"]
)

@router.get("/health")
async def database_health_check():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar_one()

        return {
            "database": "postgresql",
            "status": "ok",
            "result": value
        }

    except Exception as e:
        return {
            "database": "postgresql",
            "status": "error",
            "error": str(e)
        }
