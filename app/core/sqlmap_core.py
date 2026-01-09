from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.middleware.custom_decorators import with_async_session
from app.models.sqlmap_result import SqlmapScanPayload, SqlmapScanLog
from app.database.celery_sync_database import SessionLocal


# 初次创建任务后将会存储数据库
@with_async_session
async def task_add(
    *,
    session,
    task_id: str,
    scan_url: str,
    status: str,
    scan_risk: int = 1,
    scan_level: int = 1,
):
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


# 同步扫描任务写入。防止数据库丢失
def celery_task_add(
    *,
    session,
    task_id: str,
    scan_url: str,
    status: str,
    scan_risk: int = 1,
    scan_level: int = 1,
    celery_task_id: str,
):
    task = SqlmapScanPayload(
        task_id=task_id,
        scan_url=scan_url,
        status=status,
        scan_risk=scan_risk,
        scan_level=scan_level,
        celery_task_id=celery_task_id,
    )
    session.add(task)
    session.commit()
