"""Create saved_jobs table

Revision ID: 20260529_saved_jobs
Revises: 20260529_auth_tokens
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260529_saved_jobs"
down_revision = "20260529_auth_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_jobs",
        sa.Column("id",       UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",  UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id",   UUID(as_uuid=True), sa.ForeignKey("jobs.id",  ondelete="CASCADE"), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_saved_jobs_user_id", "saved_jobs", ["user_id"])
    op.create_index("ix_saved_jobs_job_id",  "saved_jobs", ["job_id"])
    op.create_unique_constraint("uq_saved_user_job", "saved_jobs", ["user_id", "job_id"])


def downgrade():
    op.drop_table("saved_jobs")
