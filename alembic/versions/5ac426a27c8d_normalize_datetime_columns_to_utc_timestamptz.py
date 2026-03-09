"""Normalize datetime columns to UTC timestamptz

Revision ID: 5ac426a27c8d
Revises: d3a4f84e9b7c
Create Date: 2026-03-09 02:45:00.000000
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ac426a27c8d"
down_revision: Union[str, None] = "d3a4f84e9b7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _to_timestamptz(table_name: str, column_name: str, nullable: bool) -> None:
    op.alter_column(
        table_name,
        column_name,
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=nullable,
        postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
    )


def _to_timestamp(table_name: str, column_name: str, nullable: bool) -> None:
    op.alter_column(
        table_name,
        column_name,
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=nullable,
        postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
    )


def upgrade() -> None:
    _to_timestamptz("worker_logs", "run_at", nullable=False)
    _to_timestamptz("hotdeal_keywords", "wdate", nullable=False)
    _to_timestamptz("hotdeal_keyword_sites", "wdate", nullable=False)
    _to_timestamptz("mail_logs", "sent_at", nullable=False)


def downgrade() -> None:
    _to_timestamp("mail_logs", "sent_at", nullable=False)
    _to_timestamp("hotdeal_keyword_sites", "wdate", nullable=False)
    _to_timestamp("hotdeal_keywords", "wdate", nullable=False)
    _to_timestamp("worker_logs", "run_at", nullable=False)
