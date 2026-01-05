import os
from fastapi import APIRouter, HTTPException, Body
import requests
from dotenv import load_dotenv
import app.schema.sqlmap as sqlmapschema
import app.core.sqlmap_task as sqlmap_task

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

    r = requests.get(f"{SQLMAP_API}/task/new", auth=AUTH)
    if not r.ok:
        raise HTTPException(500, "sqlmap task 创建失败")

    taskid = r.json()["taskid"]

    # 2. 启动扫描
    start = requests.post(
        f"{SQLMAP_API}/scan/{taskid}/start",
        json=payload.model_dump(mode="json"),  # json转换问题
        auth=AUTH,
    )

    await sqlmap_task.task_add(
        task_id=taskid,
        scan_url=str(payload.url),
        status="running",
        scan_risk=payload.risk,
        scan_level=payload.level,
    )

    if not start.ok:
        raise HTTPException(500, start.text)

    return {"success": True, "taskid": taskid}


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
async def task_log(task_id: str):
    r = requests.get(f"{SQLMAP_API}/scan/{task_id}/log", auth=AUTH)

    if not r.ok:
        raise HTTPException(404, "无法获取日志")

    return r.json()


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
