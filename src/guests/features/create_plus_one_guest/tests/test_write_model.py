"""Tests for SqlPlusOneGuestWriteModel."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import GuestStatus, Language, PlusOneDTO
from src.guests.features.create_guest.write_model import SqlGuestCreateWriteModel
from src.guests.features.create_plus_one_guest.write_model import (
    CannotAddPlusOneError,
    CannotChangePlusOneEmailError,
    SqlPlusOneGuestWriteModel,
)
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User


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
        result, plus_one_uuid = await plus_one_write_model.create_plus_one_guest(
            original_guest_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Verify the returned DTO
        assert result.email == "plusone@example.com"
        assert result.first_name == "Plus"
        assert result.last_name == "One"
        assert result.plus_one_of_id == original_guest.id  # Indicates this is a plus-one
        assert result.rsvp.status == GuestStatus.PENDING
        assert isinstance(result.rsvp.token, str)
        assert result.rsvp.link is not None
        assert result.rsvp.link.startswith("http://localhost:4321/en/rsvp/?token=")
        # Verify UUID is returned
        assert plus_one_uuid == result.id

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
        result, _ = await plus_one_write_model.create_plus_one_guest(
            original_guest_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Verify plus_one_of_id is set correctly in database
        guest_result = await db_session.execute(select(Guest).where(Guest.uuid == result.id))
        plus_one_guest_db = guest_result.scalar_one_or_none()

        assert plus_one_guest_db is not None
        # plus_one_of_id being set indicates this is a plus-one (no separate is_plus_one field)
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
        result, _ = await plus_one_write_model.create_plus_one_guest(
            original_guest_id=original_guest.id,
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
        result, returned_uuid = await plus_one_write_model.create_plus_one_guest(
            original_guest_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Should return the existing guest's info
        assert result.id == existing_guest.id
        assert returned_uuid == existing_guest.id
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
        result, _ = await plus_one_write_model.create_plus_one_guest(
            original_guest_id=original_guest.id,
            plus_one_data=plus_one_data,
        )

        # Verify plus-one has different RSVP token than original
        assert result.rsvp.token != original_guest.rsvp.token
        assert result.rsvp.link != original_guest.rsvp.link

        await db_session.rollback()


async def test_if_a_guest_plus_one_is_created_when_a_guest_select_a_guest_user():
    """Test that a regular guest (not a plus-one) can create a plus-one.

    The plus-one should be properly linked via plus_one_of_id and
    the original guest should have bring_a_plus_one_id set.
    """
    async with async_session_maker() as db_session:
        try:
            # Create original guest (not a plus-one)
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_plusone@test.com",
                first_name="Original",
                last_name="Guest",
            )

            # Create plus-one guest
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="plusone_select@test.com",
                first_name="Plus",
                last_name="One",
            )
            result, plus_one_uuid = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Verify plus_one_of_id is set correctly
            assert result.plus_one_of_id == original_guest.id

            # Verify the original guest has bring_a_plus_one_id set
            original_orm = await db_session.execute(
                select(Guest).where(Guest.uuid == original_guest.id)
            )
            original_guest_db = original_orm.scalar_one()
            assert original_guest_db.bring_a_plus_one_id == plus_one_uuid

            # Verify plus-one guest is properly created with user
            plus_one_orm = await db_session.execute(
                select(Guest).where(Guest.uuid == plus_one_uuid)
            )
            plus_one_guest_db = plus_one_orm.scalar_one()
            assert plus_one_guest_db.plus_one_of_id == original_guest.id
            assert plus_one_guest_db.user_id is not None
        finally:
            await db_session.rollback()


async def test_if_a_plus_one_guest_cannot_add_a_plus_one():
    """Test that a guest who is already a plus-one cannot add their own plus-one.

    Should raise CannotAddPlusOneError.
    """
    async with async_session_maker() as db_session:
        try:
            # Create original guest
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_cannot_add@test.com",
                first_name="Original",
                last_name="Guest",
            )

            # Create a plus-one guest (this guest IS a plus-one)
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="existing_plusone@test.com",
                first_name="Plus",
                last_name="One",
            )
            plus_one_result, _ = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Try to create a new plus-one for the plus-one guest
            # This should raise CannotAddPlusOneError
            new_plus_one_data = PlusOneDTO(
                email="nested_plusone@test.com",
                first_name="Nested",
                last_name="PlusOne",
            )
            with pytest.raises(CannotAddPlusOneError):
                await plus_one_write_model.create_plus_one_guest(
                    original_guest_id=plus_one_result.id,
                    plus_one_data=new_plus_one_data,
                )
        finally:
            await db_session.rollback()


async def test_if_a_plus_one_guest_also_has_a_user():
    """Test that a plus-one guest has an associated user record.

    The plus-one creation should get or create a User record.
    """
    async with async_session_maker() as db_session:
        try:
            # Create original guest
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_has_user@test.com",
                first_name="Original",
                last_name="Guest",
            )

            # Create plus-one guest
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="plusone_has_user@test.com",
                first_name="Plus",
                last_name="One",
            )
            result, plus_one_uuid = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Verify User record exists for the plus-one
            guest_result = await db_session.execute(
                select(Guest).where(Guest.uuid == plus_one_uuid)
            )
            plus_one_guest_db = guest_result.scalar_one()

            assert plus_one_guest_db.user_id is not None

            # Verify the user record exists
            user_result = await db_session.execute(
                select(User).where(User.uuid == plus_one_guest_db.user_id)
            )
            user_db = user_result.scalar_one()

            assert user_db is not None
            assert user_db.email == "plusone_has_user@test.com"
            assert user_db.is_active is True
        finally:
            await db_session.rollback()


async def test_if_a_guest_with_a_plus_one_cannot_change_the_plus_one_email():
    """Test that the email of an existing plus-one cannot be changed.

    Should raise CannotChangePlusOneEmailError when trying to change
    a plus-one's email to a different email address.
    """
    async with async_session_maker() as db_session:
        try:
            # Create original guest
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_no_change@test.com",
                first_name="Original",
                last_name="Guest",
            )

            # Create plus-one guest with initial email
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="initial_plusone@test.com",
                first_name="Plus",
                last_name="One",
            )
            result, plus_one_uuid = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Now try to create the same plus-one again but with a different email
            # This should raise CannotChangePlusOneEmailError
            changed_email_data = PlusOneDTO(
                email="changed_email@test.com",  # Different from original
                first_name="Plus",
                last_name="One",
            )

            with pytest.raises(CannotChangePlusOneEmailError):
                await plus_one_write_model.create_plus_one_guest(
                    original_guest_id=original_guest.id,
                    plus_one_data=changed_email_data,
                )
        finally:
            await db_session.rollback()


async def test_plus_one_guest_email_sent_on_default():
    """Test that email_sent_on is None by default when no email_service is set."""
    async with async_session_maker() as db_session:
        try:
            # Create original guest
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_email@test.com",
                first_name="Original",
                last_name="Guest",
            )

            # Create plus-one guest without email service
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="plusone@test.com",
                first_name="Plus",
                last_name="One",
            )
            result, _ = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Verify email_sent_on is None
            rsvp_result = await db_session.execute(
                select(RSVPInfo).where(RSVPInfo.guest_id == result.id)
            )
            rsvp_db = rsvp_result.scalar_one_or_none()
            assert rsvp_db is not None
            assert rsvp_db.email_sent_on is None
        finally:
            await db_session.rollback()


async def test_plus_one_guest_email_service_not_called_by_default():
    """Test that email_service is not called by default."""
    mock_email_service = AsyncMock()

    async with async_session_maker() as db_session:
        try:
            # Create original guest
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_nocall@test.com",
                first_name="Original",
                last_name="Guest",
            )

            # Create plus-one guest - email service is set but not called by default
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_write_model.set_email_service(mock_email_service)

            plus_one_data = PlusOneDTO(
                email="plusone_nocall@test.com",
                first_name="Plus",
                last_name="One",
            )
            result, _ = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Verify email service was NOT called (current implementation doesn't send email for plus-one)
            mock_email_service.send_invite_one_plus_one.assert_not_called()
            mock_email_service.send_invitation.assert_not_called()

            # Verify email_sent_on is None
            rsvp_result = await db_session.execute(
                select(RSVPInfo).where(RSVPInfo.guest_id == result.id)
            )
            rsvp_db = rsvp_result.scalar_one_or_none()
            assert rsvp_db.email_sent_on is None
        finally:
            await db_session.rollback()


# Language inheritance tests


async def test_plus_one_inherits_spanish_language_from_original():
    """Test that plus-one guest inherits Spanish language from original guest."""
    async with async_session_maker() as db_session:
        try:
            # Create original guest with Spanish language
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_spanish@test.com",
                first_name="Carlos",
                last_name="Garcia",
                preferred_language=Language.ES,
            )

            # Verify original guest has Spanish language
            assert original_guest.rsvp.link.startswith("http://localhost:4321/es/rsvp/?token=")

            # Create plus-one guest
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="plusone_spanish@test.com",
                first_name="Ana",
                last_name="Martinez",
            )
            result, plus_one_uuid = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Verify plus-one RSVP link has Spanish language prefix
            assert result.rsvp.link.startswith("http://localhost:4321/es/rsvp/?token=")
            assert "&plus_one=true" in result.rsvp.link

            # Verify plus-one language is Spanish in database
            guest_result = await db_session.execute(
                select(Guest).where(Guest.uuid == plus_one_uuid)
            )
            plus_one_guest_db = guest_result.scalar_one()
            assert plus_one_guest_db.preferred_language == Language.ES
        finally:
            await db_session.rollback()


async def test_plus_one_inherits_dutch_language_from_original():
    """Test that plus-one guest inherits Dutch language from original guest."""
    async with async_session_maker() as db_session:
        try:
            # Create original guest with Dutch language
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_dutch@test.com",
                first_name="Jan",
                last_name="de Vries",
                preferred_language=Language.NL,
            )

            # Verify original guest has Dutch language
            assert original_guest.rsvp.link.startswith("http://localhost:4321/nl/rsvp/?token=")

            # Create plus-one guest
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="plusone_dutch@test.com",
                first_name="Marie",
                last_name="Jansen",
            )
            result, plus_one_uuid = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Verify plus-one RSVP link has Dutch language prefix
            assert result.rsvp.link.startswith("http://localhost:4321/nl/rsvp/?token=")
            assert "&plus_one=true" in result.rsvp.link

            # Verify plus-one language is Dutch in database
            guest_result = await db_session.execute(
                select(Guest).where(Guest.uuid == plus_one_uuid)
            )
            plus_one_guest_db = guest_result.scalar_one()
            assert plus_one_guest_db.preferred_language == Language.NL
        finally:
            await db_session.rollback()


async def test_plus_one_inherits_default_english_language():
    """Test that plus-one guest inherits default English language from original guest."""
    async with async_session_maker() as db_session:
        try:
            # Create original guest with default (English) language
            guest_write_model = SqlGuestCreateWriteModel(session_overwrite=db_session)
            original_guest = await guest_write_model.create_guest(
                email="original_english@test.com",
                first_name="John",
                last_name="Smith",
            )

            # Verify original guest has English language
            assert original_guest.rsvp.link.startswith("http://localhost:4321/en/rsvp/?token=")

            # Create plus-one guest
            plus_one_write_model = SqlPlusOneGuestWriteModel(session_overwrite=db_session)
            plus_one_data = PlusOneDTO(
                email="plusone_english@test.com",
                first_name="Jane",
                last_name="Doe",
            )
            result, plus_one_uuid = await plus_one_write_model.create_plus_one_guest(
                original_guest_id=original_guest.id,
                plus_one_data=plus_one_data,
            )

            # Verify plus-one RSVP link has English language prefix
            assert result.rsvp.link.startswith("http://localhost:4321/en/rsvp/?token=")
            assert "&plus_one=true" in result.rsvp.link

            # Verify plus-one language is English in database
            guest_result = await db_session.execute(
                select(Guest).where(Guest.uuid == plus_one_uuid)
            )
            plus_one_guest_db = guest_result.scalar_one()
            assert plus_one_guest_db.preferred_language == Language.EN
        finally:
            await db_session.rollback()
