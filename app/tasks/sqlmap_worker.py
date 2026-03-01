import os
from datetime import datetime


from celery import shared_task

from app.core.async_sqlmap_api import (
    async_get,
    async_post,
    async_fetch_sqlmap_status,
    async_fetch_sqlmap_result,
)
from app.database.celery_sync_database import SessionLocal
from app.models.sqlmap_result import (
    SqlmapScanPayload,
    ScanStatus,
    SqlmapScanResult,
)
from app.core.sqlmap_core import celery_task_add
import httpx
import asyncio

SQLMAP_API = os.getenv("SQLMAP_API")
AUTH = (os.getenv("SQLMAP_USERNAME"), os.getenv("SQLMAP_PASSWORD"))  # Basic Auth


# 展平sqlmap日志
def normalize_sqlmap_result(raw: dict) -> dict:
    result = {
        "success": raw.get("success", False),
        "error": raw.get("error", []),
        "data": {"target": {}, "injections": {}, "dbms": {}},
    }

    for entry in raw.get("data", []):
        entry_type = entry.get("type")
        value = entry.get("value")

        # type 0 → 目标信息
        if entry_type == 0 and isinstance(value, dict):
            result["data"]["target"] = value

        # type 1 → 注入点（一定是 list）
        elif entry_type == 1 and isinstance(value, list):
            for item in value:
                key = f"{item.get('place')}:{item.get('parameter')}"

                result["data"]["injections"][key] = {
                    "place": item.get("place"),
                    "parameter": item.get("parameter"),
                    "ptype": item.get("ptype"),
                    "prefix": item.get("prefix"),
                    "suffix": item.get("suffix"),
                    "clause": item.get("clause"),
                    "notes": item.get("notes"),
                    "payloads": item.get("data", {}),
                }

                # DBMS 信息（只记录一次即可）
                if not result["data"]["dbms"]:
                    result["data"]["dbms"] = {
                        "name": item.get("dbms"),
                        "version": item.get("dbms_version"),
                    }

    return result


def fetch_sqlmap_result(session, task_id: str, result_json: dict):
    data = result_json.get("data", [])

    result = SqlmapScanResult(
        target_url="",
        vulnerable=bool(data),
        raw_output=data,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        command="sqlmap api scan",
    )

    session.add(result)


# 轮询运行状态任务
@shared_task(
    bind=True,
    autoretry_for=(httpx.RequestError,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def poll_single_sqlmap_task(self, sqlmap_task_id: str):
    session = SessionLocal()
    try:
        task = (
            session.query(SqlmapScanPayload)
            .filter(SqlmapScanPayload.task_id == sqlmap_task_id)
            .first()
        )
        if not task:
            return

        # 异步查询扫描状态
        status_json = asyncio.run(async_fetch_sqlmap_status(sqlmap_task_id))

        print(status_json)

        if not status_json.get("success"):
            task.status = ScanStatus.failed
            session.commit()
            return

        sqlmap_status = status_json["status"]

        if sqlmap_status == "running":
            task.status = ScanStatus.running
            session.commit()

            # 再次轮询
            self.apply_async(args=[sqlmap_task_id])
            return

        elif sqlmap_status in ("terminated", "not running"):
            task.status = ScanStatus.success
            task.finished_at = datetime.utcnow()

            result_json = asyncio.run(async_fetch_sqlmap_result(sqlmap_task_id))
            print(result_json)

            fetch_sqlmap_result(session, sqlmap_task_id, result_json)
            session.commit()
            return

        elif sqlmap_status == "error":
            task.status = ScanStatus.failed
            task.finished_at = datetime.utcnow()
            session.commit()

    finally:
        session.close()


# 用户手动创建扫描任务
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def sqlmap_scan_task(self, payload: dict):
    session = SessionLocal()
    try:
        # 异步创建 SQLMap 任务
        task_json = asyncio.run(async_get("/task/new", timeout=10))
        sqlmap_task_id = task_json["taskid"]

        # 异步启动扫描
        start_json = asyncio.run(
            async_post(f"/scan/{sqlmap_task_id}/start", json=payload, timeout=30)
        )

        # 写入数据库
        celery_task_add(
            session=session,
            task_id=sqlmap_task_id,
            celery_task_id=self.request.id,
            scan_url=str(payload["url"]),
            status="running",
            scan_risk=payload.get("risk", 1),
            scan_level=payload.get("level", 1),
        )

        return {
            "celery_task_id": self.request.id,
        }

    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()
