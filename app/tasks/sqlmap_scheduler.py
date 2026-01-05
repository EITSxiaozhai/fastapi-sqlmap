from sqlalchemy import select
from app.middleware.celery_app import celery_app
from app.database.celery_sync_database import SessionLocal
from app.models.sqlmap_result import SqlmapScanPayload, ScanStatus
from app.tasks.sqlmap_worker import poll_single_sqlmap_task


@celery_app.task(name="app.tasks.sqlmap_scheduler.poll_active_sqlmap_tasks")
def poll_active_sqlmap_tasks():
    with SessionLocal() as session:
        tasks = (
            session.query(SqlmapScanPayload)
            .filter(
                SqlmapScanPayload.status.in_([ScanStatus.pending, ScanStatus.running])
            )
            .all()
        )

        for task in tasks:
            poll_single_sqlmap_task.delay(task.task_id)
