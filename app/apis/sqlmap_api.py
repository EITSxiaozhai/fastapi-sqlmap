import os

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Body

import app.core.sqlmap_core as sqlmap_task
import app.schema.sqlmap as sqlmapschema
import app.tasks.sqlmap_worker as sqlmap_worker

router = APIRouter(prefix="/sqlmap", tags=["SQLMap扫描任务"])

load_dotenv()
SQLMAP_API = os.getenv("SQLMAP_API")
AUTH = (os.getenv("SQLMAP_USERNAME"), os.getenv("SQLMAP_PASSWORD"))  # Basic Auth


@router.post("/scan")
async def start_scan(payload: sqlmapschema.SqlmapScanPayload = Body(...)):
    """
    payload 示例:
    {
        "url": "http://testphp.vulnweb.com/listproducts.php?cat=1",
        "level": 1,
        "risk": 1
    }
    """

    celery_tasks = sqlmap_worker.sqlmap_scan_task.delay(payload.model_dump(mode="json"))

    return {
        "success": True,
        "taskid": celery_tasks.id,
    }


@router.get("/tasks")
async def list_tasks():
    tasks = await sqlmap_task.list_tasks()

    return {
        "total": len(tasks),
        "tasks": [
            {
                "task_id": t.task_id,
                "url": t.scan_url,
                "status": t.status,
                "level": t.scan_level,
                "risk": t.scan_risk,
                "created_at": t.created_at,
            }
            for t in tasks
        ],
    }


@router.get("/tasks/{task_id}")
async def task_status(task_id: str):
    r = requests.get(f"{SQLMAP_API}/scan/{task_id}/status", auth=AUTH)

    if not r.ok:
        raise HTTPException(404, "任务不存在")

    return r.json()


@router.get("/tasks/{task_id}/log")
async def task_log(task_id: str, limit: int = 100, offset: int = 0):
    logs = await sqlmap_task.get_task_logs(task_id, limit, offset)

    if not logs:
        raise HTTPException(status_code=404, detail="没有找到日志")

    return {
        "task_id": task_id,
        "logs": [
            {
                "level": log.level,
                "message": log.message,
                "log_time": log.log_time,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


@router.get("/tasks/{task_id}/result")
async def task_result(task_id: str):
    r = requests.get(f"{SQLMAP_API}/scan/{task_id}/data", auth=AUTH)

    if not r.ok:
        raise HTTPException(404, "暂无结果")

    return r.json()


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    requests.get(f"{SQLMAP_API}/scan/{task_id}/stop", auth=AUTH)

    requests.get(f"{SQLMAP_API}/task/{task_id}/delete", auth=AUTH)

    return {"success": True}
