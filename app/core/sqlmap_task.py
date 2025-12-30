from app.database.database import AsyncSessionLocal
from app.models.sqlmap_result import SqlmapScanPayload


async def task_add(
    task_id: int,
    scan_url: str,
    status: str,
    scan_risk: int = 1,
    scan_level: int = 1,
):
    async with AsyncSessionLocal() as session:
        task = SqlmapScanPayload(
            task_id=task_id,
            scan_url=scan_url,
            status=status,
            scan_risk=scan_risk,
            scan_level=scan_level,
        )
        session.add(task)
        await session.commit()
