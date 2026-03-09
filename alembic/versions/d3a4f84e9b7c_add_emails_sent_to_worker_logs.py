"""add emails_sent to worker_logs

Revision ID: d3a4f84e9b7c
Revises: 0a33b6e493e2
Create Date: 2026-03-09 02:00:00.000000
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3a4f84e9b7c"
down_revision: Union[str, None] = "0a33b6e493e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "worker_logs",
        sa.Column("emails_sent", sa.Integer(), server_default="0", nullable=False),
    )
    op.alter_column("worker_logs", "emails_sent", server_default=None)


def downgrade() -> None:
    op.drop_column("worker_logs", "emails_sent")
