"""phase2_notifications

Revision ID: 20260525_phase2
Revises: 20260524_phase1
Create Date: 2026-05-25 02:23:00.000000

Phase 2 migration — two non-destructive changes:
  1. Create `notifications` table for in-app alert records.
  2. Add `jobs_found` integer column to `scraping_runs`
     (maps to jobs_new count; added for API naming consistency).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260525_phase2'
down_revision: Union[str, None] = '20260524_phase1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create notifications table ────────────────────────────────────────
    op.create_table(
        'notifications',
        sa.Column('id',         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id',    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('job_id',     postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('jobs.id', ondelete='CASCADE'),
                  nullable=True),
        sa.Column('job_title',  sa.String(length=500),  nullable=False),
        sa.Column('score',      sa.Float(),              nullable=False),
        sa.Column('message',    sa.Text(),               nullable=True),
        sa.Column('is_read',    sa.Boolean(),
                  server_default=sa.text('false'),       nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'),       nullable=True),
    )
    op.create_index('ix_notifications_user_id',   'notifications', ['user_id'])
    op.create_index('ix_notifications_job_id',    'notifications', ['job_id'])
    op.create_index('ix_notifications_is_read',   'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at','notifications', ['created_at'])

    # ── 2. Add jobs_found to scraping_runs ───────────────────────────────────
    op.add_column('scraping_runs',
        sa.Column('jobs_found', sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('scraping_runs', 'jobs_found')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read',    table_name='notifications')
    op.drop_index('ix_notifications_job_id',     table_name='notifications')
    op.drop_index('ix_notifications_user_id',    table_name='notifications')
    op.drop_table('notifications')
