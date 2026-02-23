"""add system_config column

Revision ID: 9a2e70821b1c
Revises: 9dc0b2146133
Create Date: 2026-02-23 18:26:35.198433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a2e70821b1c'
down_revision: Union[str, Sequence[str], None] = '9dc0b2146133'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('agents', sa.Column('system_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('agents', 'system_config')
