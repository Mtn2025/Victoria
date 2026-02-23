"""Add analysis_config

Revision ID: 5e9473404f2d
Revises: 45dabae7ee5d
Create Date: 2026-02-23 15:58:19.167073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e9473404f2d'
down_revision: Union[str, Sequence[str], None] = '45dabae7ee5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('agents', sa.Column('analysis_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('agents', 'analysis_config')
