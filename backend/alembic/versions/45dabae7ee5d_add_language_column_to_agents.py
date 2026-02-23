"""Add language column to agents

Revision ID: 45dabae7ee5d
Revises: 
Create Date: 2026-02-23 02:05:55.519419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45dabae7ee5d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregamos la columna 'language' si no existe iterando sobre el bind local
    conn = op.get_bind()
    # Usamos RAW SQL condicional para evitar crashes si `create_all()` ya la creó
    conn.execute(sa.text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'es-MX'"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('agents', 'language')
