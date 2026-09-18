"""add pgvector and b2b models

Revision ID: 5709e60000c8
Revises: 
Create Date: 2026-09-18 14:58:46.216062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '5709e60000c8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Add columns to existing tables
    op.add_column('news_clusters', sa.Column('category', sa.String(), server_default='General Tech', nullable=False))
    op.add_column('news_clusters', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('user_preferences', sa.Column('preference_embedding', Vector(384), nullable=True))
    op.add_column('super_summaries', sa.Column('audio_url', sa.String(), nullable=True))
    op.add_column('super_summaries', sa.Column('audio_duration_seconds', sa.Integer(), nullable=True))

    # Create new B2B tables
    op.create_table(
        'teams',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('subscription_status', sa.String(), nullable=False, server_default='free')
    )

    op.create_table(
        'team_memberships',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('team_id', sa.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='member'),
        sa.UniqueConstraint('team_id', 'user_id', name='uq_team_membership')
    )

    op.create_table(
        'slack_installations',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('team_id', sa.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=True),
        sa.Column('workspace_id', sa.String(), nullable=False, unique=True),
        sa.Column('bot_token', sa.String(), nullable=False),
        sa.Column('channel_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    op.create_table(
        'user_email_preferences',
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('daily_digest_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('delivery_time', sa.String(), nullable=False, server_default='06:30')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_email_preferences')
    op.drop_table('slack_installations')
    op.drop_table('team_memberships')
    op.drop_table('teams')
    
    op.drop_column('super_summaries', 'audio_duration_seconds')
    op.drop_column('super_summaries', 'audio_url')
    op.drop_column('user_preferences', 'preference_embedding')
    op.drop_column('news_clusters', 'embedding')
    op.drop_column('news_clusters', 'category')
