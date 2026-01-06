from typing import Optional, List

from pydantic import BaseModel, HttpUrl, Field


class SQLMapScanRequest(BaseModel):
    target: HttpUrl = Field(..., description="扫描目标 URL")
    method: str = Field("GET", description="HTTP 方法")
    data: Optional[str] = Field(None, description="POST 数据")
    cookie: Optional[str] = None
    headers: Optional[List[str]] = None

    level: int = Field(1, ge=1, le=5)
    risk: int = Field(1, ge=1, le=3)
    threads: int = Field(1, ge=1, le=10)

    batch: bool = True
    random_agent: bool = True


class SQLMapScanResponse(BaseModel):
    task_id: int
    status: str


class SqlmapScanPayload(BaseModel):
    url: HttpUrl = Field(..., description="需要扫描的目标 URL")
    level: Optional[int] = Field(1, ge=1, le=5, description="测试级别 (1-5)")
    risk: Optional[int] = Field(1, ge=1, le=3, description="风险等级 (1-3)")
