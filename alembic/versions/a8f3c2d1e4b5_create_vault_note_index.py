"""create vault_note_index table

Revision ID: a8f3c2d1e4b5
Revises: 5caa4134853e
Create Date: 2026-06-16 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a8f3c2d1e4b5"
down_revision: Union[str, None] = "5caa4134853e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vault_note_index",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vault_path", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), server_default="", nullable=False),
        sa.Column("folder", sa.String(length=100), server_default="", nullable=False),
        sa.Column("body_snippet", sa.Text(), server_default="", nullable=False),
        sa.Column("mtime", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "indexed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vault_path", name="uq_vault_note_index_vault_path"),
    )
    op.create_index(
        "ix_vault_note_index_vault_path",
        "vault_note_index",
        ["vault_path"],
        unique=False,
    )
    op.create_index(
        "ix_vault_note_index_title",
        "vault_note_index",
        ["title"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_vault_note_index_title", table_name="vault_note_index")
    op.drop_index("ix_vault_note_index_vault_path", table_name="vault_note_index")
    op.drop_table("vault_note_index")
