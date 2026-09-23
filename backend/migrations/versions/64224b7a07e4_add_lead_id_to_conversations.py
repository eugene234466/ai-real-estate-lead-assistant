"""add lead_id to conversations

Revision ID: 64224b7a07e4
Revises: 30f044d1a014
Create Date: 2026-09-23 01:47:07.666671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64224b7a07e4'
down_revision: Union[str, Sequence[str], None] = '30f044d1a014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('conversations', sa.Column('lead_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_conversations_lead_id', 'conversations', 'leads', ['lead_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_conversations_lead_id', 'conversations', type_='foreignkey')
    op.drop_column('conversations', 'lead_id')