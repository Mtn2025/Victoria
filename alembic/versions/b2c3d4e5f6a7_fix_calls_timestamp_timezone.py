"""fix_calls_timestamp_timezone

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-21 03:12:00.000000

Defensive migration: Converts TIMESTAMP WITHOUT TIME ZONE columns to
TIMESTAMP WITH TIME ZONE in the calls and transcripts tables.

Why: asyncpg rejects inserting timezone-aware datetime objects into
TIMESTAMP WITHOUT TIME ZONE columns with:
  "can't subtract offset-naive and offset-aware datetimes"

Safe to re-run: each ALTER is wrapped in a column_type_is_timestamp
check that skips the change if the column is already TIMESTAMPTZ.

PostgreSQL only — SQLite has no distinction, so the helper gracefully
skips when the dialect is not PostgreSQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect


# revision identifiers
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

def is_postgresql() -> bool:
    """Return True when running against a PostgreSQL database."""
    bind = op.get_bind()
    return bind.dialect.name == 'postgresql'


def column_is_timestamp_without_tz(table: str, column: str) -> bool:
    """
    Return True if the column exists AND is TIMESTAMP WITHOUT TIME ZONE.
    Returns False for SQLite (no concept of tz-awareness).
    """
    if not is_postgresql():
        return False
    bind = op.get_bind()
    result = bind.execute(text("""
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = :table AND column_name = :col
    """), {"table": table, "col": column})
    row = result.fetchone()
    if not row:
        return False
    # 'timestamp without time zone' means we need to upgrade
    return row[0].lower() == 'timestamp without time zone'


def alter_to_timestamptz(table: str, column: str) -> None:
    """ALTER the column to TIMESTAMP WITH TIME ZONE (PostgreSQL only)."""
    op.execute(text(
        f"ALTER TABLE {table} "
        f"ALTER COLUMN {column} TYPE TIMESTAMP WITH TIME ZONE "
        f"USING {column} AT TIME ZONE 'UTC'"
    ))


# --------------------------------------------------------------------------- #
# Upgrade                                                                       #
# --------------------------------------------------------------------------- #

def upgrade() -> None:
    # calls.start_time
    if column_is_timestamp_without_tz('calls', 'start_time'):
        alter_to_timestamptz('calls', 'start_time')

    # calls.end_time
    if column_is_timestamp_without_tz('calls', 'end_time'):
        alter_to_timestamptz('calls', 'end_time')

    # transcripts.timestamp
    if column_is_timestamp_without_tz('transcripts', 'timestamp'):
        alter_to_timestamptz('transcripts', 'timestamp')


# --------------------------------------------------------------------------- #
# Downgrade                                                                     #
# --------------------------------------------------------------------------- #

def downgrade() -> None:
    if not is_postgresql():
        return

    op.execute(text(
        "ALTER TABLE calls "
        "ALTER COLUMN start_time TYPE TIMESTAMP WITHOUT TIME ZONE "
        "USING start_time AT TIME ZONE 'UTC'"
    ))
    op.execute(text(
        "ALTER TABLE calls "
        "ALTER COLUMN end_time TYPE TIMESTAMP WITHOUT TIME ZONE "
        "USING end_time AT TIME ZONE 'UTC'"
    ))
    op.execute(text(
        "ALTER TABLE transcripts "
        "ALTER COLUMN timestamp TYPE TIMESTAMP WITHOUT TIME ZONE "
        "USING timestamp AT TIME ZONE 'UTC'"
    ))
