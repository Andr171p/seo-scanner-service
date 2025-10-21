"""Refactor tables 1

Revision ID: 063171f4aeab
Revises: 3372b1c8be27
Create Date: 2025-10-21 17:30:32.331438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '063171f4aeab'
down_revision: Union[str, Sequence[str], None] = '3372b1c8be27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
