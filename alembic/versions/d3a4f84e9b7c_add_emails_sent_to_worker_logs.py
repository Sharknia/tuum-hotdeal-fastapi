"""add_emails_sent_to_worker_logs

Revision ID: d3a4f84e9b7c
Revises: 0a33b6e493e2
Create Date: 2026-03-09 01:28:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3a4f84e9b7c"
down_revision: Union[str, None] = "0a33b6e493e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "worker_logs",
        sa.Column("emails_sent", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("worker_logs", "emails_sent", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("worker_logs", "emails_sent")
