"""admins_table

Revision ID: c3a7f1d2e9b4
Revises: b82c9861e53f
Create Date: 2026-06-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a7f1d2e9b4'
down_revision: Union[str, Sequence[str], None] = 'b82c9861e53f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('admins',
    sa.Column('telegram_id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('added_by', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('telegram_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('admins')
