import os
from datetime import datetime

import requests
from celery import shared_task
from fastapi import HTTPException

from app.database.celery_sync_database import SessionLocal
from app.models.sqlmap_result import (
    SqlmapScanPayload,
    ScanStatus,
    SqlmapScanResult,
    SqlmapScanLog,
)
from app.core.sqlmap_core import celery_task_add

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


def fetch_sqlmap_logs(session, task: SqlmapScanPayload):
    resp = requests.get(
        f"{SQLMAP_API}/scan/{task.task_id}/log",
        auth=AUTH,
    )
    if not resp.ok:
        return

    logs = resp.json().get("log", [])

    # 已存在日志（避免重复写）
    existing = {
        (l.log_time, l.message)
        for l in session.query(SqlmapScanLog)
        .filter(SqlmapScanLog.task_id == task.task_id)
        .all()
    }

    for log in logs:
        key = (log.get("time"), log.get("message"))
        if key in existing:
            continue

        session.add(
            SqlmapScanLog(
                task_id=task.task_id,
                level=log.get("level", "INFO"),
                message=log.get("message"),
                log_time=log.get("time"),
                celery_task_id=task.celery_task_id,
            )
        )


def fetch_sqlmap_result(session, task_id: str):
    resp = requests.get(
        f"{SQLMAP_API}/scan/{task_id}/data",
        auth=AUTH,
    )
    if not resp.ok:
        return

    data = resp.json().get("data", [])

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
    autoretry_for=(requests.RequestException,),
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

        # 查询扫描状态
        status_resp = requests.get(
            f"{SQLMAP_API}/scan/{sqlmap_task_id}/status",
            auth=AUTH,
        )

        if status_resp.status_code != 200:
            task.status = ScanStatus.failed
            session.commit()
            return

        status_json = status_resp.json()
        if not status_json.get("success"):
            task.status = ScanStatus.failed
            session.commit()
            return

        sqlmap_status = status_json["status"]

        # 状态同步
        if sqlmap_status == "running":
            task.status = ScanStatus.running

        elif sqlmap_status in ("terminated", "not running"):
            task.status = ScanStatus.success
            task.finished_at = datetime.utcnow()
            fetch_sqlmap_result(session, sqlmap_task_id)

        elif sqlmap_status == "error":
            task.status = ScanStatus.failed
            task.finished_at = datetime.utcnow()

        # 同步写入日志
        fetch_sqlmap_logs(session, task)

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
        # 1. 创建 SQLMap 任务
        r = requests.get(f"{SQLMAP_API}/task/new", auth=AUTH, timeout=10)
        r.raise_for_status()
        sqlmap_task_id = r.json()["taskid"]

        # 2. 启动扫描
        start = requests.post(
            f"{SQLMAP_API}/scan/{sqlmap_task_id}/start",
            json=payload,
            auth=AUTH,
            timeout=30,
        )
        start.raise_for_status()

        # 3. 扫描启动成功后，调用 celery_task_add 写入 DB
        celery_task_add(
            session=session,
            task_id=sqlmap_task_id,
            celery_task_id=self.request.id,  # Celery 任务 ID
            scan_url=str(payload["url"]),  # 转成 str，防止 HttpUrl 错误
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
