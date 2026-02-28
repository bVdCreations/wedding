"""convert_timestamps_to_timezone_aware

Revision ID: 6743ab9ccd87
Revises: b8c9d0e1f2a3
Create Date: 2026-02-28 14:40:49.285754

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6743ab9ccd87"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ["users", "families", "dietary_options", "guests", "rsvp_info"]


def upgrade() -> None:
    for table in TABLES:
        op.alter_column(
            table,
            "created_at",
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=False),
            existing_nullable=False,
            postgresql_using=f"created_at AT TIME ZONE 'UTC'",
        )
        op.alter_column(
            table,
            "updated_at",
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=False),
            existing_nullable=False,
            postgresql_using=f"updated_at AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.alter_column(
            table,
            "updated_at",
            type_=sa.DateTime(timezone=False),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="updated_at AT TIME ZONE 'UTC'",
        )
        op.alter_column(
            table,
            "created_at",
            type_=sa.DateTime(timezone=False),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="created_at AT TIME ZONE 'UTC'",
        )
