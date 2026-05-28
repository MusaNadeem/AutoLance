"""Add job_title_snapshot to proposals

Revision ID: 20260529_proposal_title
Revises: 20260529_saved_jobs
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "20260529_proposal_title"
down_revision = "20260529_saved_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("proposals", sa.Column("job_title_snapshot", sa.String(500), nullable=True))


def downgrade():
    op.drop_column("proposals", "job_title_snapshot")
