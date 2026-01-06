from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.models.sqlmap_result import SqlmapScanPayload, SqlmapScanLog


async def task_add(
    task_id: int,
    scan_url: str,
    status: str,
    scan_risk: int = 1,
    scan_level: int = 1,
):
    async with AsyncSessionLocal() as session:
        task = SqlmapScanPayload(
            task_id=task_id,
            scan_url=scan_url,
            status=status,
            scan_risk=scan_risk,
            scan_level=scan_level,
        )
        session.add(task)
        await session.commit()


async def list_tasks():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SqlmapScanPayload).order_by(SqlmapScanPayload.created_at.desc())
        )
        return result.scalars().all()


async def get_task_logs(task_id: str, limit: int = 100, offset: int = 0):
    """
    查询指定任务的日志
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SqlmapScanLog)
            .where(SqlmapScanLog.task_id == task_id)
            .order_by(SqlmapScanLog.created_at)
            .limit(limit)
            .offset(offset)
        )
        logs = result.scalars().all()
    return logs
