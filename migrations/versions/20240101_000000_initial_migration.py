"""Initial migration - create all tables

Revision ID: 000000000000
Revises: 
Create Date: 2024-01-01 00:00:00

"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000000000000'
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4())),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_superuser', sa.Boolean, default=False),
    )

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4())),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('timezone', sa.String(50), default='UTC'),
    )

    # Create guests table
    op.create_table(
        'guests',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4())),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('event_id', sa.String(36), sa.ForeignKey('events.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'declined', name='guest_status_enum'), default='pending', nullable=False),
        sa.Column('is_plus_one', sa.Boolean, default=False),
        sa.Column('plus_one_of_id', sa.String(36), sa.ForeignKey('guests.id', ondelete='SET NULL'), nullable=True),
        sa.Column('plus_one_name', sa.String(255), nullable=True),
        sa.Column('rsvp_token', sa.String(36), nullable=False, unique=True, index=True),
        sa.Column('notes', sa.Text, nullable=True),
    )

    # Create dietary_options table
    op.create_table(
        'dietary_options',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4())),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('guest_id', sa.String(36), sa.ForeignKey('guests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('requirement_type', sa.Enum('vegetarian', 'vegan', 'gluten_free', 'dairy_free', 'halal', 'kosher', 'nut_allergy', 'other', name='dietary_type_enum'), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('dietary_options')
    op.drop_table('guests')
    op.drop_table('events')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS guest_status_enum')
    op.execute('DROP TYPE IF EXISTS dietary_type_enum')
