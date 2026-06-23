"""add embedding (pgvector) to vault_note_index

Revision ID: c1a7f0d2e8b4
Revises: b9d4e3f2a1c6
Create Date: 2026-06-23 10:00:00.000000

Aktiviert die pgvector-Extension und fuegt eine nullable ``embedding``-Spalte
fuer semantische Suche (E17-2 / E5-3) hinzu. Bewusst **kein** ANN-Index
(ivfflat/hnsw): bei persoenlicher Vault-Groesse (hunderte bis wenige tausend
Notizen) ist ein exakter kNN-Scan schnell genug und robuster. Ein ANN-Index
ist eine spaetere Skalierungs-Optimierung.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from app.models.vault_note_index import EMBEDDING_DIM

revision: str = "c1a7f0d2e8b4"
down_revision: Union[str, None] = "b9d4e3f2a1c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "vault_note_index",
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("vault_note_index", "embedding")
    # Extension bewusst NICHT droppen — koennte von anderen Objekten genutzt werden.
