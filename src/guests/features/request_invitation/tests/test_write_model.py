"""Tests for SqlRequestInvitationWriteModel."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import Language
from src.guests.features.request_invitation.write_model import (
    SqlRequestInvitationWriteModel,
)
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User

# New Guest Creation Tests


async def test_request_invitation_creates_new_user_and_guest():
    """Test requesting invitation creates User, Guest, and RSVPInfo for new email."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        email = "newuser@example.com"

        result = await write_model.request_invitation(
            email=email,
            first_name="John",
            last_name="Doe",
        )

        # Verify response
        assert result.message == "Check your email for your invitation link"

        # Verify User was created
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()
        assert user is not None
        assert user.email == email

        # Verify Guest was created
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one_or_none()
        assert guest is not None
        assert guest.first_name == "John"
        assert guest.last_name == "Doe"
        assert guest.preferred_language == Language.EN

        # Verify RSVPInfo was created
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one_or_none()
        assert rsvp is not None
        assert rsvp.status == "pending"
        assert rsvp.active is True
        assert rsvp.rsvp_token is not None
        assert rsvp.rsvp_link is not None

        await db_session.rollback()


async def test_request_invitation_with_spanish_language():
    """Test creating guest with Spanish language preference."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        email = "spanish@example.com"

        result = await write_model.request_invitation(
            email=email,
            first_name="Juan",
            last_name="Garcia",
            language=Language.ES,
        )

        assert result.message == "Check your email for your invitation link"

        # Verify Guest has Spanish language
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.preferred_language == Language.ES

        # Verify RSVP link includes Spanish prefix
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()
        assert "/es/rsvp/?token=" in rsvp.rsvp_link

        await db_session.rollback()


async def test_request_invitation_with_dutch_language():
    """Test creating guest with Dutch language preference."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        email = "dutch@example.com"

        result = await write_model.request_invitation(
            email=email,
            first_name="Jan",
            last_name="de Vries",
            language=Language.NL,
        )

        assert result.message == "Check your email for your invitation link"

        # Verify Guest has Dutch language
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.preferred_language == Language.NL

        # Verify RSVP link includes Dutch prefix
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()
        assert "/nl/rsvp/?token=" in rsvp.rsvp_link

        await db_session.rollback()


async def test_request_invitation_default_language_is_english():
    """Test that default language is English when not specified."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        email = "default@example.com"

        result = await write_model.request_invitation(
            email=email,
            first_name="Default",
            last_name="Language",
            language=None,
        )

        assert result.message == "Check your email for your invitation link"

        # Verify Guest has English language
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.preferred_language == Language.EN

        # Verify RSVP link includes English prefix
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()
        assert "/en/rsvp/?token=" in rsvp.rsvp_link

        await db_session.rollback()


# Existing Guest (Resend) Tests


async def test_request_invitation_resends_to_existing_guest():
    """Test requesting invitation for existing guest resends without creating duplicates."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        email = "existing@example.com"

        # First request - creates user/guest
        result1 = await write_model.request_invitation(
            email=email,
            first_name="Original",
            last_name="Name",
        )
        assert result1.message == "Check your email for your invitation link"

        # Get counts
        user_count = await db_session.execute(select(User))
        initial_user_count = len(user_count.scalars().all())
        guest_count = await db_session.execute(select(Guest))
        initial_guest_count = len(guest_count.scalars().all())
        rsvp_count = await db_session.execute(select(RSVPInfo))
        initial_rsvp_count = len(rsvp_count.scalars().all())

        # Get original guest data
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        original_guest = guest_result.scalar_one()
        original_first_name = original_guest.first_name
        original_last_name = original_guest.last_name

        # Second request - should resend, not create new records
        result2 = await write_model.request_invitation(
            email=email,
            first_name="Different",
            last_name="Name",
        )
        assert result2.message == "Check your email for your invitation link"

        # Verify counts stayed the same
        user_count_after = await db_session.execute(select(User))
        assert len(user_count_after.scalars().all()) == initial_user_count
        guest_count_after = await db_session.execute(select(Guest))
        assert len(guest_count_after.scalars().all()) == initial_guest_count
        rsvp_count_after = await db_session.execute(select(RSVPInfo))
        assert len(rsvp_count_after.scalars().all()) == initial_rsvp_count

        # Verify original names are NOT changed
        guest_result_after = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest_after = guest_result_after.scalar_one()
        assert guest_after.first_name == original_first_name
        assert guest_after.last_name == original_last_name

        await db_session.rollback()


async def test_request_invitation_updates_language_on_resend():
    """Test requesting invitation updates language preference on resend."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        email = "lang_update@example.com"

        # First request with English
        await write_model.request_invitation(
            email=email,
            first_name="Test",
            last_name="User",
            language=Language.EN,
        )

        # Verify initial language is English
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.preferred_language == Language.EN

        # Second request with Spanish
        await write_model.request_invitation(
            email=email,
            first_name="Test",
            last_name="User",
            language=Language.ES,
        )

        # Verify language is now Spanish
        await db_session.refresh(guest)
        assert guest.preferred_language == Language.ES

        await db_session.rollback()


async def test_request_invitation_preserves_language_when_none_on_resend():
    """Test requesting invitation preserves language when None is provided on resend."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        email = "preserve_lang@example.com"

        # First request with Spanish
        await write_model.request_invitation(
            email=email,
            first_name="Test",
            last_name="User",
            language=Language.ES,
        )

        # Verify language is Spanish
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.preferred_language == Language.ES

        # Second request with None (should preserve Spanish)
        await write_model.request_invitation(
            email=email,
            first_name="Test",
            last_name="User",
            language=None,
        )

        # Verify language is still Spanish (not changed to default)
        await db_session.refresh(guest)
        assert guest.preferred_language == Language.ES

        await db_session.rollback()


# Email Service Tests


async def test_request_invitation_sends_email_for_new_guest():
    """Test email is sent for new guest with correct parameters."""
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )

        await write_model.request_invitation(
            email="email_test@example.com",
            first_name="Email",
            last_name="Test",
            language=Language.EN,
        )

        # Verify email service was called
        mock_email_service.send_invitation.assert_called_once()

        # Verify call parameters
        call_kwargs = mock_email_service.send_invitation.call_args.kwargs
        assert call_kwargs["to_address"] == "email_test@example.com"
        assert call_kwargs["guest_name"] == "Email Test"
        assert "rsvp_url" in call_kwargs
        assert call_kwargs["language"] == Language.EN

        # Verify email_sent_on is set
        user_result = await db_session.execute(
            select(User).where(User.email == "email_test@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()
        assert rsvp.email_sent_on is not None
        assert isinstance(rsvp.email_sent_on, datetime)

        await db_session.rollback()


async def test_request_invitation_sends_email_on_resend():
    """Test email is sent when resending invitation."""
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )
        email = "resend@example.com"

        # First request
        await write_model.request_invitation(
            email=email,
            first_name="Resend",
            last_name="Test",
        )

        # Get original email_sent_on
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()

        # Reset mock
        mock_email_service.reset_mock()

        # Second request (resend)
        await write_model.request_invitation(
            email=email,
            first_name="Resend",
            last_name="Test",
        )

        # Verify email service was called again
        mock_email_service.send_invitation.assert_called_once()

        # Verify email_sent_on is updated
        await db_session.refresh(rsvp)
        assert rsvp.email_sent_on is not None
        assert isinstance(rsvp.email_sent_on, datetime)
        # Should be updated (but hard to test exact time, so just verify it exists)
        assert rsvp.email_sent_on is not None

        await db_session.rollback()


async def test_request_invitation_email_not_sent_without_service():
    """Test no error and email_sent_on is None when email service is not provided."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(
            session_overwrite=db_session, email_service=None
        )

        result = await write_model.request_invitation(
            email="noservice@example.com",
            first_name="No",
            last_name="Service",
        )

        # Should succeed
        assert result.message == "Check your email for your invitation link"

        # Verify email_sent_on is None
        user_result = await db_session.execute(
            select(User).where(User.email == "noservice@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()
        assert rsvp.email_sent_on is None

        await db_session.rollback()


async def test_request_invitation_handles_email_service_failure():
    """Test that email service failure doesn't prevent guest creation."""
    mock_email_service = AsyncMock()
    mock_email_service.send_invitation.side_effect = Exception("Email service failed")

    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )

        # Should not raise exception
        result = await write_model.request_invitation(
            email="failure@example.com",
            first_name="Failure",
            last_name="Test",
        )

        assert result.message == "Check your email for your invitation link"

        # Verify guest was still created
        user_result = await db_session.execute(
            select(User).where(User.email == "failure@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest is not None

        # Verify email_sent_on is None due to failure
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()
        assert rsvp.email_sent_on is None

        await db_session.rollback()


async def test_request_invitation_email_sent_with_correct_language():
    """Test email is sent with the correct language parameter."""
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )

        await write_model.request_invitation(
            email="spanish_email@example.com",
            first_name="Spanish",
            last_name="User",
            language=Language.ES,
        )

        # Verify email service was called with Spanish language
        mock_email_service.send_invitation.assert_called_once()
        call_kwargs = mock_email_service.send_invitation.call_args.kwargs
        assert call_kwargs["language"] == Language.ES

        await db_session.rollback()


# Edge Case Tests


async def test_request_invitation_with_existing_user_no_guest():
    """Test requesting invitation with existing user but no guest creates guest."""
    async with async_session_maker() as db_session:
        email = "user_only@example.com"

        # Create User manually (no Guest)
        user = User(
            email=email,
            hashed_password=None,
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        await db_session.flush()

        # Verify no guest exists yet
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        assert guest_result.scalar_one_or_none() is None

        # Request invitation
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        result = await write_model.request_invitation(
            email=email,
            first_name="New",
            last_name="Guest",
        )

        assert result.message == "Check your email for your invitation link"

        # Verify guest was created using existing user
        guest_result_after = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result_after.scalar_one()
        assert guest is not None
        assert guest.first_name == "New"
        assert guest.last_name == "Guest"

        # Verify only one user exists (no duplicate)
        user_count = await db_session.execute(select(User).where(User.email == email))
        assert len(user_count.scalars().all()) == 1

        await db_session.rollback()


async def test_request_invitation_empty_first_name():
    """Test requesting invitation with empty first name."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)

        result = await write_model.request_invitation(
            email="empty_first@example.com",
            first_name="",
            last_name="LastName",
        )

        assert result.message == "Check your email for your invitation link"

        # Verify guest created with empty first_name
        user_result = await db_session.execute(
            select(User).where(User.email == "empty_first@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.first_name == ""
        assert guest.last_name == "LastName"

        await db_session.rollback()


async def test_request_invitation_empty_last_name():
    """Test requesting invitation with empty last name."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)

        result = await write_model.request_invitation(
            email="empty_last@example.com",
            first_name="FirstName",
            last_name="",
        )

        assert result.message == "Check your email for your invitation link"

        # Verify guest created with empty last_name
        user_result = await db_session.execute(
            select(User).where(User.email == "empty_last@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.first_name == "FirstName"
        assert guest.last_name == ""

        await db_session.rollback()


async def test_request_invitation_whitespace_in_names():
    """Test requesting invitation with whitespace in names preserves it."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)

        result = await write_model.request_invitation(
            email="whitespace@example.com",
            first_name="  John  ",
            last_name="  Doe  ",
        )

        assert result.message == "Check your email for your invitation link"

        # Verify names are stored as-is
        user_result = await db_session.execute(
            select(User).where(User.email == "whitespace@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        assert guest.first_name == "  John  "
        assert guest.last_name == "  Doe  "

        await db_session.rollback()


async def test_request_invitation_resend_without_rsvp_info():
    """Test resending invitation when RSVPInfo is missing (data corruption scenario)."""
    async with async_session_maker() as db_session:
        email = "no_rsvp@example.com"

        # Create User and Guest manually without RSVPInfo
        user = User(
            email=email,
            hashed_password=None,
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        await db_session.flush()

        guest = Guest(
            user_id=user.uuid,
            first_name="No",
            last_name="RSVP",
            preferred_language=Language.EN,
        )
        db_session.add(guest)
        await db_session.flush()

        # Verify no RSVPInfo exists
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        assert rsvp_result.scalar_one_or_none() is None

        # Request invitation (should handle gracefully)
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)
        result = await write_model.request_invitation(
            email=email,
            first_name="Different",
            last_name="Name",
        )

        # Should succeed (resend path returns early if no RSVPInfo)
        assert result.message == "Check your email for your invitation link"

        await db_session.rollback()


# Database Integrity Tests


async def test_request_invitation_rsvp_token_is_unique_uuid():
    """Test RSVP tokens are unique UUIDs for each guest."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)

        # Create multiple guests
        await write_model.request_invitation(
            email="guest1@example.com",
            first_name="Guest",
            last_name="One",
        )
        await write_model.request_invitation(
            email="guest2@example.com",
            first_name="Guest",
            last_name="Two",
        )
        await write_model.request_invitation(
            email="guest3@example.com",
            first_name="Guest",
            last_name="Three",
        )

        # Get all RSVPInfo records
        rsvp_result = await db_session.execute(select(RSVPInfo))
        rsvps = rsvp_result.scalars().all()
        tokens = [rsvp.rsvp_token for rsvp in rsvps]

        # Verify all tokens are unique
        assert len(tokens) == len(set(tokens))

        # Verify all tokens are valid UUIDs
        for token in tokens:
            try:
                UUID(token)
            except ValueError:
                pytest.fail(f"Token {token} is not a valid UUID")

        await db_session.rollback()


async def test_request_invitation_rsvp_link_format():
    """Test RSVP link has correct format with frontend URL and token."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)

        await write_model.request_invitation(
            email="link_test@example.com",
            first_name="Link",
            last_name="Test",
            language=Language.EN,
        )

        # Get RSVPInfo
        user_result = await db_session.execute(
            select(User).where(User.email == "link_test@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()

        # Verify link format
        assert rsvp.rsvp_link.startswith("http://localhost:4321/en/rsvp/?token=")
        assert f"token={rsvp.rsvp_token}" in rsvp.rsvp_link

        await db_session.rollback()


async def test_request_invitation_creates_active_rsvp():
    """Test RSVPInfo is created with active=True and status=pending."""
    async with async_session_maker() as db_session:
        write_model = SqlRequestInvitationWriteModel(session_overwrite=db_session)

        await write_model.request_invitation(
            email="active_rsvp@example.com",
            first_name="Active",
            last_name="RSVP",
        )

        # Get RSVPInfo
        user_result = await db_session.execute(
            select(User).where(User.email == "active_rsvp@example.com")
        )
        user = user_result.scalar_one()
        guest_result = await db_session.execute(
            select(Guest).where(Guest.user_id == user.uuid)
        )
        guest = guest_result.scalar_one()
        rsvp_result = await db_session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp = rsvp_result.scalar_one()

        # Verify active and status
        assert rsvp.active is True
        assert rsvp.status == "pending"

        await db_session.rollback()
