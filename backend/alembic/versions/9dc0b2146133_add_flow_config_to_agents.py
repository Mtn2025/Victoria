"""Add flow_config to agents

Revision ID: 9dc0b2146133
Revises: 5e9473404f2d
Create Date: 2026-02-23 16:47:26.349513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9dc0b2146133'
down_revision: Union[str, Sequence[str], None] = '5e9473404f2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('agents', sa.Column('flow_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('agents', 'flow_config')
