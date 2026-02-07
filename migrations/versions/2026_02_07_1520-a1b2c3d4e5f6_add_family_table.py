"""add family table

Revision ID: a1b2c3d4e5f6
Revises: d9a53c8ac179
Create Date: 2026-02-07 15:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "d9a53c8ac179"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create families table
    op.create_table(
        "families",
        sa.Column("uuid", sa.UUID(), nullable=False, default=sa.func.gen_random_uuid()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("uuid"),
    )

    # Add family_id column to guests table
    op.add_column(
        "guests",
        sa.Column("family_id", sa.UUID(), nullable=True),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_guests_family_id_families",
        "guests",
        "families",
        ["family_id"],
        ["uuid"],
        ondelete="SET NULL",
    )

    # Create index for faster queries
    op.create_index("ix_guests_family_id", "guests", ["family_id"])


def downgrade() -> None:
    # Drop index
    op.drop_index("ix_guests_family_id", table_name="guests")

    # Drop foreign key constraint
    op.drop_constraint("fk_guests_family_id_families", "guests", type_="foreignkey")

    # Drop family_id column
    op.drop_column("guests", "family_id")

    # Drop families table
    op.drop_table("families")
