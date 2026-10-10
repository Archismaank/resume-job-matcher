"""initial_schema

Revision ID: eefbaab97155
Revises: 
Create Date: 2026-10-10 17:14:02.519410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eefbaab97155'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    No-op: TEXT and String() are identical in SQLite.
    The DB is already in the correct state — this revision just
    records the baseline so future migrations can build on top.
    """
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
