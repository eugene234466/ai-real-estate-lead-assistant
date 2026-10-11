"""add widget_key and public_token

Revision ID: 82567b05066d
Revises: d5bb9df156d4
Create Date: 2026-10-11 21:05:29.680238

"""
from typing import Sequence, Union

import secrets 
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82567b05066d'
down_revision: Union[str, Sequence[str], None] = 'd5bb9df156d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # organizations.widget_key
    op.add_column('organizations',
        sa.Column('widget_key', sa.String(length=64), nullable=True))
    for row in conn.execute(sa.text("SELECT id FROM organizations")).fetchall():
        conn.execute(
            sa.text("UPDATE organizations SET widget_key = :key WHERE id = :id"),
            {"key": secrets.token_urlsafe(24), "id": row.id}
        )
    op.alter_column('organizations', 'widget_key', nullable=False)
    op.create_index(op.f('ix_organizations_widget_key'),
                    'organizations', ['widget_key'], unique=True)

    # conversations.public_token
    op.add_column('conversations',
        sa.Column('public_token', sa.String(length=64), nullable=True))
    for row in conn.execute(sa.text("SELECT id FROM conversations")).fetchall():
        conn.execute(
            sa.text("UPDATE conversations SET public_token = :key WHERE id = :id"),
            {"key": secrets.token_urlsafe(32), "id": row.id}
        )
    op.alter_column('conversations', 'public_token', nullable=False)
    op.create_index(op.f('ix_conversations_public_token'),
                    'conversations', ['public_token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_conversations_public_token'), table_name='conversations')
    op.drop_column('conversations', 'public_token')
    op.drop_index(op.f('ix_organizations_widget_key'), table_name='organizations')
    op.drop_column('organizations', 'widget_key')
