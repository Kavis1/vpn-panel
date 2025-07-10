"""Create all tables

Revision ID: create_all_tables
Revises: create_system_events
Create Date: 2024-01-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_all_tables'
down_revision = 'create_system_events'
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

# Функция для определения типа INET в зависимости от СУБД  
def get_inet_type():
    """Возвращает подходящий тип для INET в зависимости от используемой СУБД."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return postgresql.INET()
    else:
        # Для SQLite и других СУБД используем String
        return sa.String(45)

# Функция для определения типа JSONB в зависимости от СУБД
def get_jsonb_type():
    """Возвращает подходящий тип для JSONB в зависимости от используемой СУБД."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return postgresql.JSONB(astext_type=sa.Text())
    else:
        # Для SQLite и других СУБД используем JSON
        return sa.JSON()

def upgrade() -> None:
    """Create all tables."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('telegram_id', sa.String(length=50), nullable=True),
        sa.Column('data_limit', sa.BigInteger(), nullable=True),
        sa.Column('data_used', sa.BigInteger(), default=0),
        sa.Column('device_limit', sa.Integer(), nullable=True),
        sa.Column('expire_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_notifications', sa.Boolean(), default=True),
        sa.Column('telegram_notifications', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_uuid'), 'users', ['uuid'], unique=True)

    # Create plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('data_limit', sa.BigInteger(), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('max_devices', sa.Integer(), default=3),
        sa.Column('speed_limit', sa.Integer(), nullable=True),
        sa.Column('price', sa.Float(), default=0.0),
        sa.Column('currency', sa.String(length=3), default="USD"),
        sa.Column('features', sa.JSON(), default=list),
        sa.Column('settings', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)
    op.create_index(op.f('ix_plans_is_active'), 'plans', ['is_active'], unique=False)
    op.create_index(op.f('ix_plans_name'), 'plans', ['name'], unique=False)
    op.create_index(op.f('ix_plans_uuid'), 'plans', ['uuid'], unique=True)

    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('fqdn', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_blocked', sa.Boolean(), default=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('ssh_host', sa.String(length=255), nullable=True),
        sa.Column('ssh_port', sa.Integer(), default=22),
        sa.Column('ssh_username', sa.String(length=100), nullable=True),
        sa.Column('ssh_password', sa.String(length=255), nullable=True),
        sa.Column('ssh_private_key', sa.String(length=4096), nullable=True),
        sa.Column('api_port', sa.Integer(), default=8080),
        sa.Column('api_ssl', sa.Boolean(), default=True),
        sa.Column('api_secret', sa.String(length=255), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=True),
        sa.Column('user_count', sa.Integer(), default=0),
        sa.Column('cpu_usage', sa.Float(), default=0.0),
        sa.Column('ram_usage', sa.Float(), default=0.0),
        sa.Column('disk_usage', sa.Float(), default=0.0),
        sa.Column('tags', sa.JSON(), default=list),
        sa.Column('config', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nodes_fqdn'), 'nodes', ['fqdn'], unique=True)
    op.create_index(op.f('ix_nodes_id'), 'nodes', ['id'], unique=False)
    op.create_index(op.f('ix_nodes_is_active'), 'nodes', ['is_active'], unique=False)
    op.create_index(op.f('ix_nodes_is_blocked'), 'nodes', ['is_blocked'], unique=False)
    op.create_index(op.f('ix_nodes_name'), 'nodes', ['name'], unique=False)
    op.create_index(op.f('ix_nodes_uuid'), 'nodes', ['uuid'], unique=True)

    # Create vpn_users table
    op.create_table(
        'vpn_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='ACTIVE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('traffic_limit', sa.BigInteger(), nullable=False, default=0),
        sa.Column('upload_traffic', sa.BigInteger(), nullable=False, default=0),
        sa.Column('download_traffic', sa.BigInteger(), nullable=False, default=0),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('xtls_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vpn_users_email'), 'vpn_users', ['email'], unique=True)
    op.create_index(op.f('ix_vpn_users_id'), 'vpn_users', ['id'], unique=False)
    op.create_index(op.f('ix_vpn_users_status'), 'vpn_users', ['status'], unique=False)
    op.create_index(op.f('ix_vpn_users_username'), 'vpn_users', ['username'], unique=True)
    op.create_index(op.f('ix_vpn_users_uuid'), 'vpn_users', ['uuid'], unique=True)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('auto_renew', sa.Boolean(), default=True),
        sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_used', sa.BigInteger(), default=0),
        sa.Column('settings', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_uuid'), 'subscriptions', ['uuid'], unique=True)

    # Create traffic_logs table
    op.create_table(
        'traffic_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('remote_ip', get_inet_type(), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('upload', sa.BigInteger(), default=0),
        sa.Column('download', sa.BigInteger(), default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('protocol', sa.String(length=50), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_traffic_logs_device_id'), 'traffic_logs', ['device_id'], unique=False)
    op.create_index(op.f('ix_traffic_logs_ended_at'), 'traffic_logs', ['ended_at'], unique=False)
    op.create_index(op.f('ix_traffic_logs_id'), 'traffic_logs', ['id'], unique=False)
    op.create_index(op.f('ix_traffic_logs_node_id'), 'traffic_logs', ['node_id'], unique=False)
    op.create_index(op.f('ix_traffic_logs_started_at'), 'traffic_logs', ['started_at'], unique=False)
    op.create_index(op.f('ix_traffic_logs_user_id'), 'traffic_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_traffic_logs_uuid'), 'traffic_logs', ['uuid'], unique=True)

    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('device_model', sa.String(length=100), nullable=True),
        sa.Column('os_name', sa.String(length=50), nullable=True),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.Column('app_version', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('last_active', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_trusted', sa.Boolean(), default=False),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vpn_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vpn_user_id'], ['vpn_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_device_id'), 'devices', ['device_id'], unique=True)
    op.create_index(op.f('ix_devices_id'), 'devices', ['id'], unique=False)

    # Create additional tables
    # Create config_versions table
    op.create_table(
        'config_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', get_jsonb_type(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_config_versions_checksum'), 'config_versions', ['checksum'], unique=False)
    op.create_index(op.f('ix_config_versions_id'), 'config_versions', ['id'], unique=False)
    op.create_index(op.f('ix_config_versions_version'), 'config_versions', ['version'], unique=True)

    # Create config_syncs table
    op.create_table(
        'config_syncs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='PENDING'),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('last_attempt', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('metadata', get_jsonb_type(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('config_version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['config_version_id'], ['config_versions.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_config_syncs_id'), 'config_syncs', ['id'], unique=False)

    # Create xray_configs table
    op.create_table(
        'xray_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_xray_configs_checksum'), 'xray_configs', ['checksum'], unique=True)
    op.create_index(op.f('ix_xray_configs_id'), 'xray_configs', ['id'], unique=False)
    op.create_index(op.f('ix_xray_configs_is_active'), 'xray_configs', ['is_active'], unique=False)
    op.create_index(op.f('ix_xray_configs_version'), 'xray_configs', ['version'], unique=True)

    # Create traffic_limits table
    op.create_table(
        'traffic_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', get_uuid_type(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_limit', sa.BigInteger(), nullable=True),
        sa.Column('data_used', sa.BigInteger(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_traffic_limits_id'), 'traffic_limits', ['id'], unique=False)
    op.create_index(op.f('ix_traffic_limits_period_end'), 'traffic_limits', ['period_end'], unique=False)
    op.create_index(op.f('ix_traffic_limits_period_start'), 'traffic_limits', ['period_start'], unique=False)
    op.create_index(op.f('ix_traffic_limits_period_type'), 'traffic_limits', ['period_type'], unique=False)
    op.create_index(op.f('ix_traffic_limits_user_id'), 'traffic_limits', ['user_id'], unique=False)
    op.create_index(op.f('ix_traffic_limits_uuid'), 'traffic_limits', ['uuid'], unique=True)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('traffic_limits')
    op.drop_table('xray_configs')
    op.drop_table('config_syncs')
    op.drop_table('config_versions')
    op.drop_table('devices')
    op.drop_table('traffic_logs')
    op.drop_table('subscriptions')
    op.drop_table('vpn_users')
    op.drop_table('nodes')
    op.drop_table('plans')
    op.drop_table('users')