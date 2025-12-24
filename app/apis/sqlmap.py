from fastapi import APIRouter

router = APIRouter(
    prefix="/sqlmap",
    tags=["SQLMap扫描任务"]
)

@router.get("/tasks")
async def list_tasks():
    return {"msg": "list sqlmap tasks"}

@router.post("/scan")
async def start_scan():
    return {"msg": "start sqlmap scan"}
