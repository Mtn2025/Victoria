"""add_agent_uuid_is_active_created_at

Revision ID: a1b2c3d4e5f6
Revises: 4936acd0ce6c
Create Date: 2026-02-20 19:54:00.000000

Defensive migration: each column is only added if it does not already
exist in the table. Re-running this migration on an already-migrated
database is safe and idempotent.

PostgreSQL-only: uses gen_random_uuid() (pgcrypto built-in).
NOT compatible with SQLite.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4936acd0ce6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

def column_exists(table: str, column: str) -> bool:
    """Return True if *column* already exists in *table*."""
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [c['name'] for c in insp.get_columns(table)]
    return column in columns


# --------------------------------------------------------------------------- #
# Upgrade                                                                       #
# --------------------------------------------------------------------------- #

def upgrade() -> None:
    """
    Add agent_uuid, is_active, and created_at columns to the agents table.

    Each column is guarded by column_exists() so this script is safe to
    re-apply on a database where the columns were already created manually
    or by a previous partial run.

    After adding agent_uuid:
      - Fills all existing rows with gen_random_uuid().
      - Promotes agent id=3 (name='default') to is_active=true.
    """

    # ------------------------------------------------------------------ #
    # agent_uuid                                                           #
    # ------------------------------------------------------------------ #
    if not column_exists('agents', 'agent_uuid'):
        op.add_column('agents',
            sa.Column('agent_uuid', sa.String(36), nullable=True, unique=True)
        )
        # Fill existing rows before enforcing NOT NULL
        op.execute(text(
            "UPDATE agents SET agent_uuid = gen_random_uuid()::text"
        ))
        op.alter_column('agents', 'agent_uuid', nullable=False)

    # ------------------------------------------------------------------ #
    # is_active                                                            #
    # ------------------------------------------------------------------ #
    if not column_exists('agents', 'is_active'):
        op.add_column('agents',
            sa.Column('is_active', sa.Boolean(), nullable=False,
                      server_default=sa.text('false'))
        )
        # Activate the only known agent (id=3, name='default')
        op.execute(text(
            "UPDATE agents SET is_active = true WHERE id = 3"
        ))

    # ------------------------------------------------------------------ #
    # created_at                                                           #
    # ------------------------------------------------------------------ #
    if not column_exists('agents', 'created_at'):
        op.add_column('agents',
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False)
        )


# --------------------------------------------------------------------------- #
# Downgrade                                                                     #
# --------------------------------------------------------------------------- #

def downgrade() -> None:
    """
    Remove the three columns added by upgrade(), only if they currently exist.
    """
    bind = op.get_bind()
    insp = inspect(bind)
    existing = [c['name'] for c in insp.get_columns('agents')]

    for col in ['created_at', 'is_active', 'agent_uuid']:
        if col in existing:
            op.drop_column('agents', col)
