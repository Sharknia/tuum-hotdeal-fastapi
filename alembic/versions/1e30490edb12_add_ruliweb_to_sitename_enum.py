"""add_ruliweb_fmkorea_to_sitename_enum

Revision ID: 1e30490edb12
Revises: c616424fda8c
Create Date: 2026-01-23

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1e30490edb12"
down_revision: Union[str, None] = "c616424fda8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE sitename ADD VALUE IF NOT EXISTS 'RULIWEB'")
    op.execute("ALTER TYPE sitename ADD VALUE IF NOT EXISTS 'FMKOREA'")


def downgrade() -> None:
    pass
