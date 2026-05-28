"""Add reset_token and verification_token to users

Revision ID: 20260529_auth_tokens
Revises: 20260525_phase3
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "20260529_auth_tokens"
down_revision = "20260525_phase3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("reset_token", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("verification_token", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("users", "verification_token")
    op.drop_column("users", "reset_token_expires")
    op.drop_column("users", "reset_token")
