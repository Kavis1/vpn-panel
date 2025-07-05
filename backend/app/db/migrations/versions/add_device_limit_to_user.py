"""Add device_limit to User

Revision ID: 1234567890ab
Revises: 
Create Date: 2025-07-06 00:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add device_limit column to users table
    op.add_column('users', sa.Column('device_limit', sa.Integer(), nullable=True, 
                  comment='Максимальное количество устройств, NULL = использовать значение по умолчанию'))
    
    # Create an index on device_limit for faster queries
    op.create_index(op.f('ix_users_device_limit'), 'users', ['device_limit'], unique=False)


def downgrade():
    # Drop the index and column when rolling back
    op.drop_index(op.f('ix_users_device_limit'), table_name='users')
    op.drop_column('users', 'device_limit')
