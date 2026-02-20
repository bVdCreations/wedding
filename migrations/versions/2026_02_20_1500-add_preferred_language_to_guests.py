"""Add preferred_language column to guests table.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-02-20 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add preferred_language column to guests table."""
    # Create the enum type
    language_enum = sa.Enum("en", "es", "nl", name="language_enum")
    language_enum.create(op.get_bind(), checkfirst=True)

    # Add the column with default value 'en'
    op.add_column(
        "guests",
        sa.Column(
            "preferred_language",
            language_enum,
            nullable=False,
            server_default="en",
        ),
    )


def downgrade() -> None:
    """Remove preferred_language column from guests table."""
    op.drop_column("guests", "preferred_language")

    # Drop the enum type
    sa.Enum(name="language_enum").drop(op.get_bind(), checkfirst=True)
