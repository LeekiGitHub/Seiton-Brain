"""add vault_chunk table for document chunking (E18-4)

Revision ID: e3f9c5b2a8d1
Revises: d2e8b4a1c7f0
Create Date: 2026-07-27 10:00:00.000000

Eine Notiz kann N Chunks haben. Embeddings fuer Retrieval wandern auf die
Chunk-Ebene; ``vault_note_index.embedding`` bleibt (nullable) fuer
Rueckwaertskompatibilitaet.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from app.models.vault_note_index import EMBEDDING_DIM

revision: str = "e3f9c5b2a8d1"
down_revision: Union[str, None] = "d2e8b4a1c7f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vault_chunk",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("vault_note_index.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.UniqueConstraint("note_id", "chunk_index", name="uq_vault_chunk_note_index"),
    )
    op.create_index("ix_vault_chunk_note_id", "vault_chunk", ["note_id"])


def downgrade() -> None:
    op.drop_index("ix_vault_chunk_note_id", table_name="vault_chunk")
    op.drop_table("vault_chunk")
