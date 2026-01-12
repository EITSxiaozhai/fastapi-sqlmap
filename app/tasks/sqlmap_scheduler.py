from celery import shared_task

from app.database.celery_sync_database import SessionLocal
from app.models.sqlmap_result import SqlmapScanPayload, ScanStatus
from app.tasks.sqlmap_worker import poll_single_sqlmap_task


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def poll_active_sqlmap_tasks(self):
    """
    轮询所有 pending / running 的 sqlmap 任务
    """
    session = SessionLocal()
    try:
        tasks = (
            session.query(SqlmapScanPayload)
            .filter(
                SqlmapScanPayload.status.in_([ScanStatus.pending, ScanStatus.running])
            )
            .all()
        )

        for task in tasks:
            poll_single_sqlmap_task.delay(task.task_id)

    finally:
        session.close()
