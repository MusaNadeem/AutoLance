"""
Phase 3 Migration — add target_fixed_min/max to freelancer_profiles
Revision ID: 20260525_phase3
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260525_phase3"
down_revision: Union[str, None] = "20260525_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "freelancer_profiles",
        sa.Column("target_fixed_min", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "freelancer_profiles",
        sa.Column("target_fixed_max", sa.Numeric(10, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("freelancer_profiles", "target_fixed_max")
    op.drop_column("freelancer_profiles", "target_fixed_min")
