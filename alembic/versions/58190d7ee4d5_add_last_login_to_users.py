"""add_last_login_to_users

Revision ID: 58190d7ee4d5
Revises: ba0fb53dce89
Create Date: 2026-01-27 10:16:13.610455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '58190d7ee4d5'
down_revision: Union[str, None] = 'ba0fb53dce89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column exists to handle inconsistent DB state
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'last_login' not in columns:
        op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'last_login')
