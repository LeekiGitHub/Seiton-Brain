"""add doc_type to vault_note_index

Revision ID: b9d4e3f2a1c6
Revises: a8f3c2d1e4b5
Create Date: 2026-06-19 15:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b9d4e3f2a1c6"
down_revision: Union[str, None] = "a8f3c2d1e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vault_note_index",
        sa.Column(
            "doc_type",
            sa.String(length=30),
            server_default="markdown",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_vault_note_index_doc_type",
        "vault_note_index",
        ["doc_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_vault_note_index_doc_type", table_name="vault_note_index")
    op.drop_column("vault_note_index", "doc_type")
