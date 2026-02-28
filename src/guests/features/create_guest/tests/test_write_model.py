"""Tests for SqlGuestCreateWriteModel."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import GuestAlreadyExistsError, GuestStatus, Language
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
        assert result.rsvp.link.startswith("http://localhost:4321/en/rsvp/?token=")
        # New guests are not plus-ones by default (plus_one_of_id is None)
        assert result.plus_one_of_id is None


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


async def test_create_guest_basic():
    """Test creating a basic guest without special attributes."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="basic@example.com",
            first_name="Basic",
            last_name="Guest",
        )

        # Basic guest creation - no plus_one_of_id (not a plus-one)
        assert result.plus_one_of_id is None
        assert result.bring_a_plus_one_id is None
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
        # email_sent_on is None when no email_service is provided
        assert rsvp_db.email_sent_on is None
        await db_session.rollback()


async def test_create_guest_email_sent_on_without_service():
    """Test email_sent_on is None when no email_service is provided."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="noservice@example.com",
            first_name="No",
            last_name="Service",
            send_email=True,  # Explicitly set to True but no email_service
        )

        result_db = await db_session.execute(
            select(RSVPInfo).join(Guest).where(Guest.uuid == result.id)
        )
        rsvp_db = result_db.scalar_one_or_none()
        assert rsvp_db is not None
        assert rsvp_db.email_sent_on is None
        await db_session.rollback()


async def test_create_guest_send_email_false():
    """Test email_sent_on is None when send_email is False."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="noemail@example.com",
            first_name="No",
            last_name="Email",
            send_email=False,
        )

        result_db = await db_session.execute(
            select(RSVPInfo).join(Guest).where(Guest.uuid == result.id)
        )
        rsvp_db = result_db.scalar_one_or_none()
        assert rsvp_db is not None
        assert rsvp_db.email_sent_on is None
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


async def test_create_guest_with_email_service_sets_timestamp():
    """Test that email_sent_on is set when email_service is provided and send_email=True."""
    # Create a mock email service
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )
        result = await write_model.create_guest(
            email="withservice@example.com",
            first_name="With",
            last_name="Service",
            send_email=True,
        )

        result_db = await db_session.execute(
            select(RSVPInfo).join(Guest).where(Guest.uuid == result.id)
        )
        rsvp_db = result_db.scalar_one_or_none()
        assert rsvp_db is not None
        # email_sent_on should be set when email_service is provided
        assert rsvp_db.email_sent_on is not None
        assert isinstance(rsvp_db.email_sent_on, datetime)
        await db_session.rollback()


async def test_create_guest_email_service_is_called():
    """Test that email_service.send_invitation is called when send_email=True."""
    # Create a mock email service
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )
        await write_model.create_guest(
            email="testcall@example.com",
            first_name="Test",
            last_name="Call",
            send_email=True,
        )

        # Verify the email service was called
        mock_email_service.send_invitation.assert_called_once()

        # Verify the call arguments
        call_kwargs = mock_email_service.send_invitation.call_args.kwargs
        assert call_kwargs["to_address"] == "testcall@example.com"
        assert call_kwargs["guest_name"] == "Test Call"
        assert "rsvp_url" in call_kwargs

        await db_session.rollback()


async def test_create_guest_email_service_not_called_when_send_email_false():
    """Test that email_service is NOT called when send_email=False."""
    # Create a mock email service
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )
        result = await write_model.create_guest(
            email="notcalled@example.com",
            first_name="Not",
            last_name="Called",
            send_email=False,
        )

        # Verify the email service was NOT called
        mock_email_service.send_invitation.assert_not_called()

        # Verify email_sent_on is None
        result_db = await db_session.execute(
            select(RSVPInfo).join(Guest).where(Guest.uuid == result.id)
        )
        rsvp_db = result_db.scalar_one_or_none()
        assert rsvp_db is not None
        assert rsvp_db.email_sent_on is None

        await db_session.rollback()


async def test_create_guest_email_service_not_called_without_service():
    """Test that email_service is NOT called when no email_service is provided."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session, email_service=None)
        result = await write_model.create_guest(
            email="nopservice@example.com",
            first_name="No",
            last_name="Service",
            send_email=True,
        )

        # Verify email_sent_on is None when no service provided
        result_db = await db_session.execute(
            select(RSVPInfo).join(Guest).where(Guest.uuid == result.id)
        )
        rsvp_db = result_db.scalar_one_or_none()
        assert rsvp_db is not None
        assert rsvp_db.email_sent_on is None

        await db_session.rollback()


# Language-specific tests


async def test_create_guest_with_spanish_language():
    """Test creating a guest with Spanish language preference."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="spanish@example.com",
            first_name="Juan",
            last_name="Garcia",
            preferred_language=Language.ES,
        )

        # Verify RSVP link includes Spanish language prefix
        assert result.rsvp.link.startswith("http://localhost:4321/es/rsvp/?token=")

        # Verify language is stored in database
        result_db = await db_session.execute(select(Guest).where(Guest.uuid == result.id))
        guest_db = result_db.scalar_one_or_none()
        assert guest_db is not None
        assert guest_db.preferred_language == Language.ES

        await db_session.rollback()


async def test_create_guest_with_dutch_language():
    """Test creating a guest with Dutch language preference."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="dutch@example.com",
            first_name="Jan",
            last_name="de Vries",
            preferred_language=Language.NL,
        )

        # Verify RSVP link includes Dutch language prefix
        assert result.rsvp.link.startswith("http://localhost:4321/nl/rsvp/?token=")

        # Verify language is stored in database
        result_db = await db_session.execute(select(Guest).where(Guest.uuid == result.id))
        guest_db = result_db.scalar_one_or_none()
        assert guest_db is not None
        assert guest_db.preferred_language == Language.NL

        await db_session.rollback()


async def test_create_guest_default_language_is_english():
    """Test that default language is English when not specified."""
    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
        result = await write_model.create_guest(
            email="default_lang@example.com",
            first_name="Default",
            last_name="Language",
        )

        # Verify RSVP link uses English prefix by default
        assert result.rsvp.link.startswith("http://localhost:4321/en/rsvp/?token=")

        # Verify language is English in database
        result_db = await db_session.execute(select(Guest).where(Guest.uuid == result.id))
        guest_db = result_db.scalar_one_or_none()
        assert guest_db is not None
        assert guest_db.preferred_language == Language.EN

        await db_session.rollback()


async def test_create_guest_email_sent_with_correct_language():
    """Test that email is sent with the correct language parameter."""
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )
        await write_model.create_guest(
            email="spanish_email@example.com",
            first_name="Maria",
            last_name="Lopez",
            preferred_language=Language.ES,
            send_email=True,
        )

        # Verify the email service was called with Spanish language
        mock_email_service.send_invitation.assert_called_once()
        call_kwargs = mock_email_service.send_invitation.call_args.kwargs
        assert call_kwargs["language"] == Language.ES

        await db_session.rollback()


async def test_create_guest_email_sent_with_dutch_language():
    """Test that email is sent with Dutch language parameter."""
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )
        await write_model.create_guest(
            email="dutch_email@example.com",
            first_name="Pieter",
            last_name="Jansen",
            preferred_language=Language.NL,
            send_email=True,
        )

        # Verify the email service was called with Dutch language
        mock_email_service.send_invitation.assert_called_once()
        call_kwargs = mock_email_service.send_invitation.call_args.kwargs
        assert call_kwargs["language"] == Language.NL

        await db_session.rollback()
