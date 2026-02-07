"""remove plus_one redundant fields (is_plus_one, plus_one_name)

Revision ID: d9a53c8ac179
Revises: 70e6186c5a09
Create Date: 2026-02-07 14:45:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9a53c8ac179"
down_revision = "70e6186c5a09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Fix existing bring_a_plus_one_id values by finding guests who have plus-ones
    # Set bring_a_plus_one_id on original guests where plus-ones exist
    op.execute("""
        UPDATE guests g1
        SET bring_a_plus_one_id = g2.uuid
        FROM guests g2
        WHERE g2.plus_one_of_id = g1.uuid
        AND g1.bring_a_plus_one_id IS NULL
    """)

    # 2. Drop the redundant columns
    op.drop_column("guests", "plus_one_name")
    op.drop_column("guests", "is_plus_one")


def downgrade() -> None:
    # Re-add the columns
    op.add_column(
        "guests",
        sa.Column("is_plus_one", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "guests",
        sa.Column("plus_one_name", sa.String(255), nullable=True),
    )

    # Repopulate is_plus_one from plus_one_of_id
    op.execute("""
        UPDATE guests
        SET is_plus_one = true
        WHERE plus_one_of_id IS NOT NULL
    """)

    # Repopulate plus_one_name from joined data
    op.execute("""
        UPDATE guests g1
        SET plus_one_name = CONCAT(g2.first_name, ' ', g2.last_name)
        FROM guests g2
        WHERE g1.bring_a_plus_one_id = g2.uuid
    """)
