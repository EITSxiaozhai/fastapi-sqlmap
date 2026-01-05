"""add sqlmap_task_results status enum

Revision ID: ebfb414b1fbc
Revises: 8420a4c060b6
Create Date: 2026-01-05 11:56:05.347143
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebfb414b1fbc'
down_revision: Union[str, Sequence[str], None] = '8420a4c060b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1️⃣ 创建 ENUM 类型
    scan_status_enum = sa.Enum(
        'pending',
        'running',
        'success',
        'failed',
        'stopped',
        name='scan_status_enum'
    )
    scan_status_enum.create(op.get_bind(), checkfirst=True)

    # 2️⃣ BOOLEAN -> ENUM（使用 USING 显式转换）
    op.execute(
        """
        ALTER TABLE sqlmap_task_results
        ALTER COLUMN status DROP DEFAULT,
        ALTER COLUMN status TYPE scan_status_enum
        USING (
            CASE
                WHEN status = true THEN 'running'
                ELSE 'pending'
            END
        )::scan_status_enum
        """
    )

    # 3️⃣ 设置默认值
    op.execute(
        "ALTER TABLE sqlmap_task_results ALTER COLUMN status SET DEFAULT 'pending'"
    )


def downgrade() -> None:
    # ENUM -> BOOLEAN
    op.execute(
        """
        ALTER TABLE sqlmap_task_results
        ALTER COLUMN status DROP DEFAULT,
        ALTER COLUMN status TYPE BOOLEAN
        USING (
            CASE
                WHEN status IN ('running', 'success') THEN true
                ELSE false
            END
        )
        """
    )

    sa.Enum(name='scan_status_enum').drop(op.get_bind(), checkfirst=True)
