"""add prompt_version to entries

Revision ID: d2e8b4a1c7f0
Revises: c1a7f0d2e8b4
Create Date: 2026-07-22 06:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2e8b4a1c7f0"
down_revision: Union[str, None] = "c1a7f0d2e8b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "entries",
        sa.Column("prompt_version", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("entries", "prompt_version")
