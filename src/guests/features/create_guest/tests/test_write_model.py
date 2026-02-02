"""Tests for SqlGuestCreateWriteModel."""

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import GuestAlreadyExistsError, GuestStatus
from src.guests.features.create_guest.write_model import (
    SqlGuestCreateWriteModel,
)
from src.guests.repository.orm_models import Guest, RSVPInfo


async def test_create_guest_new_user():
    """Test creating a guest with a new user (email doesn't exist)."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        email = "newuser@example.com"

        result = await write_model.create_guest(
            email=email,
            first_name="John",
            last_name="Doe",
        )

        await db_session.rollback()
        # Verify the returned DTO
        assert result.email == email
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        assert result.rsvp.status == GuestStatus.PENDING
        assert isinstance(result.rsvp.token, str)
        assert result.rsvp.link is not None
        assert result.rsvp.link.startswith("http://localhost:4321/rsvp/?token=")
        assert result.is_plus_one is False
        assert result.plus_one_name is None


async def test_create_guest_existing_user():
    """Test creating a guest when user already exists raises GuestAlreadyExistsError."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        email = "existing@example.com"

        # Create first guest
        result1 = await write_model.create_guest(
            email=email,
            first_name="First",
            last_name="Guest",
        )

        # Verify first guest was created
        assert result1.email == email
        assert result1.first_name == "First"
        assert result1.last_name == "Guest"

        with pytest.raises(GuestAlreadyExistsError) as exc_info:
            await write_model.create_guest(
                email=email,
                first_name="Second",
                last_name="Guest",
            )
            assert exc_info.value.email == email
        await db_session.rollback()


async def test_create_guest_without_names():
    """Test creating a guest without names."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="nonames@example.com",
            first_name=None,
            last_name=None,
        )

        # Should handle missing names gracefully
        assert result.first_name is None
        assert result.last_name is None
        await db_session.rollback()


async def test_create_guest_with_only_first_name():
    """Test creating a guest with only first_name."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="firstname@example.com",
            first_name="Single",
            last_name=None,
        )

        assert result.first_name == "Single"
        await db_session.rollback()


async def test_create_guest_with_only_last_name():
    """Test creating a guest with only last_name."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="lastname@example.com",
            first_name=None,
            last_name="Name",
        )

        assert result.last_name == "Name"
        await db_session.rollback()


async def test_create_guest_with_plus_one():
    """Test creating a guest with plus one."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="plusone@example.com",
            first_name="Main",
            last_name="Guest",
            is_plus_one=True,
            plus_one_name="Plus One Name",
        )

        assert result.is_plus_one is True
        assert result.plus_one_name == "Plus One Name"
        await db_session.rollback()


async def test_create_guest_with_phone():
    """Test creating a guest with phone number."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="phone@example.com",
            first_name="Phone",
            last_name="Guest",
            phone="+1234567890",
        )

        result_db = await db_session.execute(select(Guest).where(Guest.uuid == result.id))
        guest_db = result_db.scalar_one_or_none()
        assert guest_db is not None
        assert guest_db.phone == "+1234567890"
        await db_session.rollback()


async def test_create_guest_with_notes():
    """Test creating a guest with notes."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="notes@example.com",
            first_name="Note",
            last_name="Guest",
            notes="Some special notes",
        )

        result_db = await db_session.execute(select(Guest).where(Guest.uuid == result.id))
        guest_db = result_db.scalar_one_or_none()
        assert guest_db is not None
        assert guest_db.notes == "Some special notes"
        await db_session.rollback()


async def test_create_guest_creates_rsvp_info():
    """Test that creating a guest also creates RSVPInfo."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="rsvp@example.com",
            first_name="RSVP",
            last_name="Guest",
        )

        result_db = await db_session.execute(
            select(RSVPInfo).join(Guest).where(Guest.uuid == result.id)
        )
        rsvp_db = result_db.scalar_one_or_none()
        assert rsvp_db is not None
        assert rsvp_db.status == GuestStatus.PENDING
        assert rsvp_db.active is True
        assert rsvp_db.rsvp_token is not None
        assert rsvp_db.rsvp_link is not None
        await db_session.rollback()


async def test_create_guest_duplicate_guest_raises_error():
    """Test that creating a guest for a user who already has one raises GuestAlreadyExistsError."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        email = "duplicate@example.com"

        # Create first guest
        result1 = await write_model.create_guest(
            email=email,
            first_name="First",
            last_name="Guest",
        )
        assert result1.email == email

        # Try to create a second guest with the same email
        with pytest.raises(GuestAlreadyExistsError) as exc_info:
            await write_model.create_guest(
                email=email,
                first_name="Second",
                last_name="Guest",
            )

        # Verify the exception contains the correct email
        assert exc_info.value.email == email
        await db_session.rollback()
