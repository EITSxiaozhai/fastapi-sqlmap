import requests
from datetime import datetime
from celery import shared_task
from app.database.celery_sync_database import SessionLocal
from app.models.sqlmap_result import (
    SqlmapScanPayload,
    ScanStatus,
    SqlmapScanResult,
)
import os

SQLMAP_API = os.getenv("SQLMAP_API")
AUTH = (os.getenv("SQLMAP_USERNAME"), os.getenv("SQLMAP_PASSWORD"))  # Basic Auth


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


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
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

        # 展平sqlmap返回日志
        normalized = normalize_sqlmap_result(data)

        print(normalized)

        # 解析 sqlmap 返回
        scan_result = SqlmapScanResult(
            target_url=normalized["data"]["target"]["url"],
            dbms=normalized["data"]["dbms"].get("name"),
            vulnerable=bool(normalized["data"]["injections"]),
            injection_points=normalized["data"]["injections"],
            dump_data=None,  # 后续支持 sqlmap dump 再填
            raw_output=normalized,
            command="",
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
