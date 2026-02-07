"""Tests for SqlPlusOneGuestWriteModel."""

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import GuestStatus, PlusOneDTO
from src.guests.features.create_guest.write_model import SqlGuestCreateWriteModel
from src.guests.features.create_plus_one_guest.write_model import (
    SqlPlusOneGuestWriteModel,
)
from src.guests.repository.orm_models import Guest, RSVPInfo


async def test_create_plus_one_guest_new_user():
    """Test creating a plus-one guest with a new user."""
    async with async_session_maker() as db_session:
        # First create an original guest
        guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        original_guest = await guest_write_model.create_guest(
            email="original@example.com",
            first_name="Original",
            last_name="Guest",
        )

        # Create plus-one guest
        plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
        plus_one_data = PlusOneDTO(
            email="plusone@example.com",
            first_name="Plus",
            last_name="One",
        )
        result = await plus_one_write_model.create_plus_one_guest(
            original_guest_user_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Verify the returned DTO
        assert result.email == "plusone@example.com"
        assert result.first_name == "Plus"
        assert result.last_name == "One"
        assert result.is_plus_one is True
        assert result.rsvp.status == GuestStatus.PENDING
        assert isinstance(result.rsvp.token, str)
        assert result.rsvp.link is not None
        assert result.rsvp.link.startswith("http://localhost:4321/rsvp/?token=")

        await db_session.rollback()


async def test_create_plus_one_guest_links_to_original():
    """Test that plus-one guest is linked to the original guest via plus_one_of_id."""
    async with async_session_maker() as db_session:
        # Create original guest
        guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        original_guest = await guest_write_model.create_guest(
            email="original2@example.com",
            first_name="Original",
            last_name="Guest",
        )

        # Create plus-one guest
        plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
        plus_one_data = PlusOneDTO(
            email="plusone2@example.com",
            first_name="Plus",
            last_name="Two",
        )
        result = await plus_one_write_model.create_plus_one_guest(
            original_guest_user_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Verify plus_one_of_id is set correctly in database
        guest_result = await db_session.execute(
            select(Guest).where(Guest.uuid == result.id)
        )
        plus_one_guest_db = guest_result.scalar_one_or_none()

        assert plus_one_guest_db is not None
        assert plus_one_guest_db.is_plus_one is True
        assert plus_one_guest_db.plus_one_of_id == original_guest.id

        await db_session.rollback()


async def test_create_plus_one_guest_creates_rsvp_info():
    """Test that creating a plus-one guest also creates RSVPInfo."""
    async with async_session_maker() as db_session:
        # Create original guest
        guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        original_guest = await guest_write_model.create_guest(
            email="original3@example.com",
            first_name="Original",
            last_name="Guest",
        )

        # Create plus-one guest
        plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
        plus_one_data = PlusOneDTO(
            email="plusone3@example.com",
            first_name="Plus",
            last_name="Three",
        )
        result = await plus_one_write_model.create_plus_one_guest(
            original_guest_user_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Verify RSVPInfo was created
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == result.id)
        )
        rsvp_db = rsvp_result.scalar_one_or_none()

        assert rsvp_db is not None
        assert rsvp_db.status == GuestStatus.PENDING
        assert rsvp_db.active is True
        assert rsvp_db.rsvp_token == result.rsvp.token
        assert rsvp_db.rsvp_link == result.rsvp.link

        await db_session.rollback()


async def test_create_plus_one_guest_existing_user_returns_existing_guest():
    """Test that creating a plus-one guest for existing user returns their existing info."""
    async with async_session_maker() as db_session:
        # Create original guest
        guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        original_guest = await guest_write_model.create_guest(
            email="original4@example.com",
            first_name="Original",
            last_name="Guest",
        )

        # Create a guest that will be the "existing" plus-one
        existing_guest = await guest_write_model.create_guest(
            email="existing_plusone@example.com",
            first_name="Existing",
            last_name="PlusOne",
        )

        # Try to create a plus-one with the same email as existing guest
        plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
        plus_one_data = PlusOneDTO(
            email="existing_plusone@example.com",
            first_name="Different",
            last_name="Name",
        )
        result = await plus_one_write_model.create_plus_one_guest(
            original_guest_user_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Should return the existing guest's info
        assert result.id == existing_guest.id
        assert result.first_name == "Existing"
        assert result.last_name == "PlusOne"
        assert result.rsvp.token == existing_guest.rsvp.token

        await db_session.rollback()


async def test_create_plus_one_guest_has_independent_rsvp():
    """Test that plus-one guest has their own independent RSVP token."""
    async with async_session_maker() as db_session:
        # Create original guest
        guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        original_guest = await guest_write_model.create_guest(
            email="original5@example.com",
            first_name="Original",
            last_name="Guest",
        )

        # Create plus-one guest
        plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
        plus_one_data = PlusOneDTO(
            email="plusone5@example.com",
            first_name="Plus",
            last_name="Five",
        )
        result = await plus_one_write_model.create_plus_one_guest(
            original_guest_user_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Verify plus-one has different RSVP token than original
        assert result.rsvp.token != original_guest.rsvp.token
        assert result.rsvp.link != original_guest.rsvp.link

        await db_session.rollback()
