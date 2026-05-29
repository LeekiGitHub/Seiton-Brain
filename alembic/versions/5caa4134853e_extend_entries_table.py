"""extend entries with telegram, raw_input, vault_path, status, kind

Revision ID: 5caa4134853e
Revises: f153d8ce8963
Create Date: 2026-05-29 10:25:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "5caa4134853e"
down_revision: Union[str, None] = "f153d8ce8963"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "entries", sa.Column("raw_input", sa.Text(), nullable=True)
    )
    op.add_column(
        "entries", sa.Column("vault_path", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "entries", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "entries", sa.Column("telegram_message_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "entries", sa.Column("telegram_update_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "entries",
        sa.Column(
            "kind",
            sa.String(length=10),
            nullable=False,
            server_default="text",
        ),
    )
    op.add_column(
        "entries",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="processed",
        ),
    )

    op.create_index(
        "ix_entries_telegram_chat_id",
        "entries",
        ["telegram_chat_id"],
    )
    op.create_unique_constraint(
        "uq_entries_telegram_update_id",
        "entries",
        ["telegram_update_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_entries_telegram_update_id", "entries", type_="unique"
    )
    op.drop_index("ix_entries_telegram_chat_id", table_name="entries")
    op.drop_column("entries", "status")
    op.drop_column("entries", "kind")
    op.drop_column("entries", "telegram_update_id")
    op.drop_column("entries", "telegram_message_id")
    op.drop_column("entries", "telegram_chat_id")
    op.drop_column("entries", "vault_path")
    op.drop_column("entries", "raw_input")
