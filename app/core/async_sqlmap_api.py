import httpx
import os
from dotenv import load_dotenv

load_dotenv()
SQLMAP_API = os.getenv("SQLMAP_API")
AUTH = (os.getenv("SQLMAP_USERNAME"), os.getenv("SQLMAP_PASSWORD"))  # Basic Auth


# 异步 HTTP 封装
async def async_get(path: str, timeout=10):
    async with httpx.AsyncClient(auth=AUTH, timeout=timeout) as client:
        resp = await client.get(f"{SQLMAP_API}{path}")
        resp.raise_for_status()
        return resp.json()


async def async_post(path: str, json=None, timeout=30):
    async with httpx.AsyncClient(auth=AUTH, timeout=timeout) as client:
        resp = await client.post(f"{SQLMAP_API}{path}", json=json)
        resp.raise_for_status()
        return resp.json()


# 异步获取日志
async def async_fetch_sqlmap_logs(task_id: str):
    return await async_get(f"/scan/{task_id}/log")


# 异步获取扫描状态
async def async_fetch_sqlmap_status(task_id: str):
    return await async_get(f"/scan/{task_id}/status")


# 异步获取扫描结果
async def async_fetch_sqlmap_result(task_id: str):
    return await async_get(f"/scan/{task_id}/data")
