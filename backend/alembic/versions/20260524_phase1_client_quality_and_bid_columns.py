"""add_phase1_client_quality_and_bid_columns

Revision ID: 20260524_phase1
Revises: b45adee43753
Create Date: 2026-05-24 21:16:00.000000

Phase 1 migration — adds 6 nullable columns to the jobs table.
All columns are nullable with no server_default so existing rows
are not touched and remain fully intact.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260524_phase1'
down_revision: Union[str, None] = 'b45adee43753'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Client quality score (Float, 0.0 – 1.0) ──────────────────────────────
    op.add_column('jobs',
        sa.Column('client_quality_score', sa.Float(), nullable=True)
    )

    # ── Bid strategy fields ───────────────────────────────────────────────────
    op.add_column('jobs',
        sa.Column('bid_strategy', sa.String(length=20), nullable=True)
    )
    op.add_column('jobs',
        sa.Column('bid_rationale', sa.Text(), nullable=True)
    )
    op.add_column('jobs',
        sa.Column('bid_confidence', sa.Float(), nullable=True)
    )
    op.add_column('jobs',
        sa.Column('bid_range_min', sa.Numeric(precision=12, scale=2), nullable=True)
    )
    op.add_column('jobs',
        sa.Column('bid_range_max', sa.Numeric(precision=12, scale=2), nullable=True)
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_column('jobs', 'bid_range_max')
    op.drop_column('jobs', 'bid_range_min')
    op.drop_column('jobs', 'bid_confidence')
    op.drop_column('jobs', 'bid_rationale')
    op.drop_column('jobs', 'bid_strategy')
    op.drop_column('jobs', 'client_quality_score')
