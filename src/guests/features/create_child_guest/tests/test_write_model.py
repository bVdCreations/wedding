"""Tests for child guest creation write model."""

from datetime import datetime

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import GuestStatus, GuestType
from src.guests.features.create_child_guest.write_model import (
    SqlChildGuestCreateWriteModel,
)
from src.guests.repository.orm_models import Family, Guest, RSVPInfo


async def test_create_child_guest_success():
    """Test creating a child guest successfully."""
    async with async_session_maker() as session:
        # Create a family first with timestamps
        now = datetime.utcnow()
        family = Family(
            name="Test Family",
            created_at=now,
            updated_at=now,
        )
        session.add(family)
        await session.flush()

        # Create child guest
        write_model = SqlChildGuestCreateWriteModel(session_overwrite=session)
        guest = await write_model.create_child_guest(
            family_id=family.uuid,
            first_name="Bobby",
            last_name="Smith",
            phone="+1234567890",
        )

        # Verify the guest was created
        assert guest is not None
        assert guest.id is not None
        assert guest.first_name == "Bobby"
        assert guest.last_name == "Smith"
        assert guest.phone == "+1234567890"
        assert guest.email == ""
        assert guest.family_id == family.uuid

        # Verify RSVP info
        assert guest.rsvp is not None
        assert guest.rsvp.status == GuestStatus.PENDING
        assert guest.rsvp.token == ""
        assert guest.rsvp.link == ""

        await session.rollback()


async def test_create_child_guest_without_phone():
    """Test creating a child guest without phone."""
    async with async_session_maker() as session:
        # Create a family
        now = datetime.utcnow()
        family = Family(name="Test Family", created_at=now, updated_at=now)
        session.add(family)
        await session.flush()

        # Create child guest without phone
        write_model = SqlChildGuestCreateWriteModel(session_overwrite=session)
        guest = await write_model.create_child_guest(
            family_id=family.uuid,
            first_name="Alice",
            last_name="Smith",
        )

        # Verify
        assert guest.first_name == "Alice"
        assert guest.last_name == "Smith"
        assert guest.phone is None

        await session.rollback()


async def test_create_child_guest_invalid_family():
    """Test that creating a child guest with invalid family raises error."""
    from uuid import uuid4

    async with async_session_maker() as session:
        write_model = SqlChildGuestCreateWriteModel(session_overwrite=session)

        with pytest.raises(ValueError, match="Family not found"):
            await write_model.create_child_guest(
                family_id=uuid4(),
                first_name="Bobby",
                last_name="Smith",
            )


async def test_create_child_guest_guest_type_is_child():
    """Test that created guest has guest_type=CHILD."""
    async with async_session_maker() as session:
        now = datetime.utcnow()
        family = Family(name="Test Family", created_at=now, updated_at=now)
        session.add(family)
        await session.flush()

        write_model = SqlChildGuestCreateWriteModel(session_overwrite=session)
        await write_model.create_child_guest(
            family_id=family.uuid,
            first_name="Bobby",
            last_name="Smith",
        )
        await session.flush()

        # Query the guest to verify guest_type
        stmt = select(Guest).where(Guest.first_name == "Bobby")
        result = await session.execute(stmt)
        guest = result.scalar_one()

        assert guest.guest_type == GuestType.CHILD
        assert guest.user_id is None

        await session.rollback()


async def test_create_child_guest_has_rsvp_info():
    """Test that child guest has RSVPInfo with empty token/link."""
    async with async_session_maker() as session:
        now = datetime.utcnow()
        family = Family(name="Test Family", created_at=now, updated_at=now)
        session.add(family)
        await session.flush()

        write_model = SqlChildGuestCreateWriteModel(session_overwrite=session)
        guest = await write_model.create_child_guest(
            family_id=family.uuid,
            first_name="Bobby",
            last_name="Smith",
        )

        # Query RSVP info
        stmt = select(RSVPInfo).where(RSVPInfo.guest_id == guest.id)
        result = await session.execute(stmt)
        rsvp_info = result.scalar_one()

        assert rsvp_info is not None
        assert rsvp_info.status == GuestStatus.PENDING
        assert rsvp_info.active is True
        assert rsvp_info.rsvp_token == ""
        assert rsvp_info.rsvp_link == ""

        await session.rollback()
