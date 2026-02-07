"""add guest_type column and make user_id nullable

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-07 16:38:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create guest_type enum
    op.execute("CREATE TYPE guest_type_enum AS ENUM ('adult', 'child')")

    # Add guest_type column as nullable first
    op.add_column(
        "guests",
        sa.Column("guest_type", sa.String(20), nullable=True),
    )

    # Update existing records to 'adult'
    op.execute("UPDATE guests SET guest_type = 'adult' WHERE guest_type IS NULL")

    # Now alter to use the enum type and set NOT NULL
    op.execute("ALTER TABLE guests ALTER COLUMN guest_type TYPE VARCHAR(20)")
    op.execute("ALTER TABLE guests ALTER COLUMN guest_type SET NOT NULL")

    # Make user_id nullable (for children without User)
    op.alter_column("guests", "user_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    # Make user_id NOT NULL again
    op.alter_column("guests", "user_id", existing_type=sa.UUID(), nullable=False)

    # Drop guest_type column
    op.drop_column("guests", "guest_type")

    # Drop guest_type enum
    op.execute("DROP TYPE guest_type_enum")
