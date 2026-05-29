"""Widen cv_documents.file_type to fit long MIME types (DOCX = 73 chars)

Revision ID: 20260529_cv_filetype
Revises: 20260529_proposal_title
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "20260529_cv_filetype"
down_revision = "20260529_proposal_title"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "cv_documents", "file_type",
        type_=sa.String(150),
        existing_type=sa.String(50),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "cv_documents", "file_type",
        type_=sa.String(50),
        existing_type=sa.String(150),
        existing_nullable=True,
    )
