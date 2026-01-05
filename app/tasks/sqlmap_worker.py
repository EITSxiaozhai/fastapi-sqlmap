import asyncio
import requests
from celery import shared_task
from datetime import datetime
from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.models.sqlmap_result import (
    SqlmapScanPayload,
    SqlmapScanLog,
    ScanStatus,
)
import os

SQLMAP_API = os.getenv("SQLMAP_API")
AUTH = (os.getenv("SQLMAP_USERNAME"), os.getenv("SQLMAP_PASSWORD"))


def fetch_status(task_id: str) -> dict:
    r = requests.get(f"{SQLMAP_API}/scan/{task_id}/status", auth=AUTH, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_log(task_id: str) -> dict:
    r = requests.get(f"{SQLMAP_API}/scan/{task_id}/log", auth=AUTH, timeout=10)
    r.raise_for_status()
    return r.json()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def poll_single_sqlmap_task(self, task_id: str):
    """
    Worker：轮询单个 sqlmap 任务
    """

    async def _run():
        async with AsyncSessionLocal() as session:
            task = await session.scalar(
                select(SqlmapScanPayload).where(SqlmapScanPayload.task_id == task_id)
            )

            if not task:
                return

            # 已结束 → 不再轮询
            if task.status in (
                ScanStatus.success,
                ScanStatus.failed,
                ScanStatus.stopped,
            ):
                return

            # --- 调 sqlmap ---
            status_data = fetch_status(task_id)
            log_data = fetch_log(task_id)

            sqlmap_status = status_data.get("status")

            # --- 状态映射 ---
            if sqlmap_status == "running":
                task.status = ScanStatus.running

            elif sqlmap_status == "terminated":
                task.status = ScanStatus.success
                task.finished_at = datetime.utcnow()

            elif sqlmap_status == "error":
                task.status = ScanStatus.failed
                task.finished_at = datetime.utcnow()

            # --- 写日志（全量 or 增量）---
            for item in log_data.get("log", []):
                session.add(
                    SqlmapScanLog(
                        task_id=task_id,
                        level=item.get("level", "INFO"),
                        message=item.get("message", ""),
                        log_time=item.get("time"),
                    )
                )

            await session.commit()

    asyncio.run(_run())
