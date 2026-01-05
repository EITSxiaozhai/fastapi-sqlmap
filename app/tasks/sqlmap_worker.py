import requests
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from app.middleware.celery_app import celery_app
from app.database.celery_sync_database import SessionLocal
from app.models.sqlmap_result import (
    SqlmapScanPayload,
    SqlmapScanLog,
    ScanStatus,
    SqlmapScanResult,
)
import os

SQLMAP_API = os.getenv("SQLMAP_API")
AUTH = (os.getenv("SQLMAP_USERNAME"), os.getenv("SQLMAP_PASSWORD"))  # Basic Auth


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
    name="app.tasks.sqlmap_worker.poll_single_sqlmap_task",
)
def poll_single_sqlmap_task(self, task_id: str):
    session = SessionLocal()
    try:
        task = (
            session.query(SqlmapScanPayload)
            .filter(SqlmapScanPayload.task_id == task_id)
            .first()
        )

        if not task:
            return

        # 查询 sqlmap task 状态
        resp = requests.get(
            f"{SQLMAP_API}/scan/{task_id}/status",
            timeout=10,
            auth=AUTH,
        )
        resp.raise_for_status()
        status_data = resp.json()

        status = status_data.get("status")

        if status == "running":
            task.status = ScanStatus.running
            session.commit()
            return

        if status != "terminated":
            return

        # 获取扫描结果
        result_resp = requests.get(
            f"{SQLMAP_API}/scan/{task_id}/data",
            timeout=30,
            auth=AUTH,
        )
        result_resp.raise_for_status()
        data = result_resp.json()

        # 解析 sqlmap 返回
        scan_result = SqlmapScanResult(
            target_url=task.scan_url,
            dbms=data.get("dbms"),
            vulnerable=bool(data.get("data")),
            injection_points=data.get("data"),
            dump_data=data.get("dump"),
            raw_output=data.get("raw"),
            command=data.get("command", ""),
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
        )

        session.add(scan_result)
        task.status = ScanStatus.success

        session.commit()

    except Exception:
        session.rollback()
        task.status = ScanStatus.failed
        session.commit()
        raise
    finally:
        session.close()
