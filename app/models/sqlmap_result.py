from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

Base = declarative_base()

class SqlmapScanResult(Base):
    __tablename__ = "sqlmap_scan_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 扫描目标
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # 识别到的数据库类型（MySQL / PostgreSQL / MSSQL 等）
    dbms: Mapped[str | None] = mapped_column(String(64))

    # 是否存在 SQL 注入
    vulnerable: Mapped[bool] = mapped_column(Boolean, default=False)

    # 注入点信息（sqlmap --json-output）
    injection_points: Mapped[dict | None] = mapped_column(JSONB)

    # dump 出的数据（表 / 字段 / 行）
    dump_data: Mapped[dict | None] = mapped_column(JSONB)

    # 原始输出（stdout）
    raw_output: Mapped[str | None] = mapped_column(Text)

    # 实际执行的 sqlmap 命令
    command: Mapped[str] = mapped_column(Text, nullable=False)

    # 时间
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
