import asyncio
from celery import shared_task
from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.models.sqlmap_result import SqlmapScanPayload, ScanStatus
from app.tasks.sqlmap_worker import poll_single_sqlmap_task


# 轮询查询数据库中的正在运行状态的数据
@shared_task
def poll_active_sqlmap_tasks():
    async def _run():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SqlmapScanPayload).where(
                    SqlmapScanPayload.status.in_(
                        [ScanStatus.pending, ScanStatus.running]
                    )
                )
            )
            tasks = result.scalars().all()

            for task in tasks:
                poll_single_sqlmap_task.delay(task.task_id)

    asyncio.run(_run())
