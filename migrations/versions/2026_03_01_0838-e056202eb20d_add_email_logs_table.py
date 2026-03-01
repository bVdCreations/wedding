"""add_email_logs_table

Revision ID: e056202eb20d
Revises: 6743ab9ccd87
Create Date: 2026-03-01 08:38:18.671430

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e056202eb20d"
down_revision = "6743ab9ccd87"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_logs table
    # SQLAlchemy will handle enum creation with checkfirst
    op.create_table(
        "email_logs",
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("resend_email_id", sa.String(length=255), nullable=True),
        sa.Column("to_address", sa.String(length=255), nullable=False),
        sa.Column("from_address", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=True),
        sa.Column("text_body", sa.Text(), nullable=True),
        sa.Column(
            "email_type",
            sa.Enum(
                "invitation",
                "confirmation",
                "reminder",
                "plus_one_invite",
                "forwarded",
                name="email_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("guest_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "sent",
                "delivered",
                "bounced",
                "failed",
                "complained",
                name="email_status_enum",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("language", sa.Enum("en", "nl", name="language_enum_ref"), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_webhook_event", sa.String(length=100), nullable=True),
        sa.Column("last_webhook_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.uuid"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.uuid"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("uuid"),
    )

    # Create indexes
    op.create_index("ix_email_logs_resend_email_id", "email_logs", ["resend_email_id"], unique=True)
    op.create_index("ix_email_logs_to_address", "email_logs", ["to_address"])
    op.create_index("ix_email_logs_email_type", "email_logs", ["email_type"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])
    op.create_index("ix_email_logs_guest_id", "email_logs", ["guest_id"])
    op.create_index("ix_email_logs_user_id", "email_logs", ["user_id"])
    op.create_index("ix_email_logs_created_at", "email_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_email_logs_created_at", table_name="email_logs")
    op.drop_index("ix_email_logs_user_id", table_name="email_logs")
    op.drop_index("ix_email_logs_guest_id", table_name="email_logs")
    op.drop_index("ix_email_logs_status", table_name="email_logs")
    op.drop_index("ix_email_logs_email_type", table_name="email_logs")
    op.drop_index("ix_email_logs_to_address", table_name="email_logs")
    op.drop_index("ix_email_logs_resend_email_id", table_name="email_logs")
    op.drop_table("email_logs")
    op.execute("DROP TYPE email_status_enum")
    op.execute("DROP TYPE email_type_enum")
