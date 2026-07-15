"""add person avatar_id

Revision ID: 9deefac4ff11
Revises: f58c3113f516
Create Date: 2026-07-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9deefac4ff11'
down_revision = 'f58c3113f516'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('people', schema=None) as batch_op:
        batch_op.add_column(sa.Column('avatar_id', sa.String(length=30), nullable=True))


def downgrade():
    with op.batch_alter_table('people', schema=None) as batch_op:
        batch_op.drop_column('avatar_id')
