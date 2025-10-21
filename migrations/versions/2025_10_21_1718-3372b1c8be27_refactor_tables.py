"""Refactor tables

Revision ID: 3372b1c8be27
Revises: 0942b08dc3ca
Create Date: 2025-10-21 17:18:06.867631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3372b1c8be27'
down_revision: Union[str, Sequence[str], None] = '0942b08dc3ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
