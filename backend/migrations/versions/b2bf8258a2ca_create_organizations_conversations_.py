"""create organizations conversations messages

Revision ID: b2bf8258a2ca
Revises: f89e265937c9
Create Date: 2026-09-18 20:07:00.466615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2bf8258a2ca'
down_revision: Union[str, Sequence[str], None] = 'f89e265937c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
