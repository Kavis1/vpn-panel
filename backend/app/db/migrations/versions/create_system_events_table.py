"""Create system_events table

Revision ID: create_system_events
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_system_events'
down_revision = None
branch_labels = None
depends_on = None

# Функция для определения типа UUID в зависимости от СУБД
def get_uuid_type():
    """Возвращает подходящий тип для UUID в зависимости от используемой СУБД."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return postgresql.UUID(as_uuid=True)
    else:
        # Для SQLite и других СУБД используем String
        return sa.String(36)

def upgrade() -> None:
    """Create system_events table."""
    # Create system_events table
    op.create_table(
        'system_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_system_events_id', 'system_events', ['id'])
    op.create_index('ix_system_events_uuid', 'system_events', ['uuid'], unique=True)
    op.create_index('ix_system_events_timestamp', 'system_events', ['timestamp'])
    op.create_index('ix_system_events_level', 'system_events', ['level'])
    op.create_index('ix_system_events_source', 'system_events', ['source'])
    op.create_index('ix_system_events_category', 'system_events', ['category'])
    op.create_index('ix_system_events_user_id', 'system_events', ['user_id'])
    op.create_index('ix_system_events_node_id', 'system_events', ['node_id'])
    
    # Create composite indexes for optimization
    op.create_index('ix_system_events_timestamp_level', 'system_events', ['timestamp', 'level'])
    op.create_index('ix_system_events_source_category', 'system_events', ['source', 'category'])
    op.create_index('ix_system_events_user_timestamp', 'system_events', ['user_id', 'timestamp'])
    op.create_index('ix_system_events_node_timestamp', 'system_events', ['node_id', 'timestamp'])


def downgrade() -> None:
    """Drop system_events table."""
    # Drop indexes first
    op.drop_index('ix_system_events_node_timestamp', table_name='system_events')
    op.drop_index('ix_system_events_user_timestamp', table_name='system_events')
    op.drop_index('ix_system_events_source_category', table_name='system_events')
    op.drop_index('ix_system_events_timestamp_level', table_name='system_events')
    op.drop_index('ix_system_events_node_id', table_name='system_events')
    op.drop_index('ix_system_events_user_id', table_name='system_events')
    op.drop_index('ix_system_events_category', table_name='system_events')
    op.drop_index('ix_system_events_source', table_name='system_events')
    op.drop_index('ix_system_events_level', table_name='system_events')
    op.drop_index('ix_system_events_timestamp', table_name='system_events')
    op.drop_index('ix_system_events_uuid', table_name='system_events')
    op.drop_index('ix_system_events_id', table_name='system_events')
    
    # Drop table
    op.drop_table('system_events')