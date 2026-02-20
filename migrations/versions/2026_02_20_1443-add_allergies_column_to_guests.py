"""Add allergies column to guests table.

Revision ID: a7b8c9d0e1f2
Revises: d6ea7082a6f2
Create Date: 2026-02-20 14:43:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "d6ea7082a6f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add allergies column to guests table."""
    op.add_column("guests", sa.Column("allergies", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove allergies column from guests table."""
    op.drop_column("guests", "allergies")
