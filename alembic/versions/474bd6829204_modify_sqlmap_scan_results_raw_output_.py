"""modify sqlmap_scan_results  raw_output tables

Revision ID: 474bd6829204
Revises: ebfb414b1fbc
Create Date: 2026-01-06 15:11:59.665084

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "474bd6829204"
down_revision: Union[str, Sequence[str], None] = "ebfb414b1fbc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 强制 TEXT -> JSONB
    op.execute(
        "ALTER TABLE sqlmap_scan_results ALTER COLUMN raw_output TYPE JSONB USING raw_output::jsonb;"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 强制 JSONB -> TEXT
    op.execute(
        "ALTER TABLE sqlmap_scan_results ALTER COLUMN raw_output TYPE TEXT USING raw_output::text;"
    )
