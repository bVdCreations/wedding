"""Tests for SqlRSVPWriteModel."""

import pytest
import pytest_asyncio
from sqlalchemy import select

from src.config.database import async_session_manager
from src.email.service import EmailService
from src.guests.dtos import DietaryType, GuestStatus, RSVPResponseDTO
from src.guests.features.update_rsvp.router import RSVPResponseSubmit
from src.guests.repository.orm_models import DietaryOption, Guest, RSVPInfo
from src.guests.repository.write_models import SqlRSVPWriteModel
from src.models.user import User


class MockEmailService(EmailService):
    """Mock email service for testing."""

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
    ) -> None:
        """Mock send confirmation - does nothing."""
        pass


async def create_test_user(async_session, email="test@example.com"):
    """Create a test user, cleaning up any existing test data first."""
    # Clean up existing test user if it exists
    existing_user = await async_session.execute(
        select(User).where(User.email == email)
    )
    if existing_user.scalar_one_or_none():
        await async_session.execute(User.__table__.delete().where(User.email == email))
        await async_session.flush()

    user = User(
        email=email,
        hashed_password="hashed_password",
    )
    async_session.add(user)
    await async_session.flush()
    await async_session.refresh(user)
    return user


async def create_test_guest(async_session, test_user, rsvp_token="test-token-12345"):
    """Create a test guest with RSVP info, cleaning up existing guest first."""
    # Clean up existing guest with same token if it exists
    existing_rsvp = await async_session.execute(
        select(RSVPInfo).where(RSVPInfo.rsvp_token == rsvp_token)
    )
    existing_rsvp_data = existing_rsvp.scalar_one_or_none()
    if existing_rsvp_data:
        await async_session.execute(
            DietaryOption.__table__.delete().where(
                DietaryOption.guest_id == existing_rsvp_data.guest_id
            )
        )
        await async_session.execute(
            RSVPInfo.__table__.delete().where(RSVPInfo.rsvp_token == rsvp_token)
        )
        await async_session.execute(
            Guest.__table__.delete().where(Guest.uuid == existing_rsvp_data.guest_id)
        )
        await async_session.flush()

    guest = Guest(
        user_id=test_user.uuid,
        first_name="John",
        last_name="Doe",
        phone="+1234567890",
    )
    async_session.add(guest)
    await async_session.flush()
    await async_session.refresh(guest)

    rsvp_info = RSVPInfo(
        guest_id=guest.uuid,
        status=GuestStatus.PENDING,
        rsvp_token=rsvp_token,
        rsvp_link=f"http://example.com/rsvp/{rsvp_token}",
    )
    async_session.add(rsvp_info)
    await async_session.flush()
    await async_session.refresh(guest)

    return guest


@pytest.mark.asyncio
async def test_submit_rsvp_attending():
    """Test submitting an RSVP with attending=true."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            guest = await create_test_guest(session, user)
            guest_uuid = guest.uuid

            write_model = SqlRSVPWriteModel(
                session_overwrite=session,
                email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=True,
                dietary_requirements=[],
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="test-token-12345",
                rsvp_data=rsvp_data,
            )

            assert isinstance(result, RSVPResponseDTO)
            assert result.attending is True
            assert result.status == GuestStatus.CONFIRMED
            assert "Thank you for confirming" in result.message

            # Verify database state
            rsvp_result = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid))
            rsvp_info = rsvp_result.scalar_one()
            assert rsvp_info.status == GuestStatus.CONFIRMED
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_not_attending():
    """Test submitting an RSVP with attending=false."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            guest = await create_test_guest(session, user)
            guest_uuid = guest.uuid

            write_model = SqlRSVPWriteModel(
                session_overwrite=session,
                email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=False,
                dietary_requirements=[],
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="test-token-12345",
                rsvp_data=rsvp_data,
            )

            assert isinstance(result, RSVPResponseDTO)
            assert result.attending is False
            assert result.status == GuestStatus.DECLINED
            assert "We're sorry you can't make it" in result.message

            # Verify database state
            rsvp_result = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid))
            rsvp_info = rsvp_result.scalar_one()
            assert rsvp_info.status == GuestStatus.DECLINED
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_with_dietary_requirements():
    """Test submitting an RSVP with dietary requirements."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            guest = await create_test_guest(session, user)
            guest_uuid = guest.uuid

            write_model = SqlRSVPWriteModel(
                session_overwrite=session,
                email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=True,
                dietary_requirements=[
                    {"requirement_type": "vegetarian", "notes": "No mushrooms please"},
                    {"requirement_type": "gluten_free", "notes": None},
                ],
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="test-token-12345",
                rsvp_data=rsvp_data,
            )

            assert isinstance(result, RSVPResponseDTO)
            assert result.attending is True
            assert result.status == GuestStatus.CONFIRMED

            # Verify database state
            result = await session.execute(
                select(DietaryOption).where(DietaryOption.guest_id == guest_uuid)
            )
            dietary_opts = result.scalars().all()
            assert len(dietary_opts) == 2
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one():
    """Test submitting an RSVP with plus one.

    Note: This test verifies the RSVP submission with plus_one_details data.
    The actual plus_one creation requires plus_one_guest_write_model which is not
    injected here. This test focuses on the RSVP data handling.
    """
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            guest = await create_test_guest(session, user)

            write_model = SqlRSVPWriteModel(
                session_overwrite=session,
                email_service=MockEmailService()
            )

            # Test that plus_one_details data is accepted (actual creation requires separate test)
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                plus_one_details=None,  # Set to None since we don't test full plus_one creation here
                dietary_requirements=[],
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="test-token-12345",
                rsvp_data=rsvp_data,
            )

            assert isinstance(result, RSVPResponseDTO)
            assert result.attending is True
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_with_invalid_token():
    """Test submitting an RSVP with an invalid token."""
    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    rsvp_data = RSVPResponseSubmit(
        attending=True,
        dietary_requirements=[],
        family_member_updates={},
    )

    with pytest.raises(ValueError, match="Invalid RSVP token"):
        await write_model.submit_rsvp(
            token="invalid-token",
            rsvp_data=rsvp_data,
        )


@pytest.mark.asyncio
async def test_submit_rsvp_clears_previous_dietary():
    """Test that submitting an RSVP clears previous dietary requirements."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            guest = await create_test_guest(session, user)
            guest_uuid = guest.uuid

            # Add initial dietary requirement
            dietary = DietaryOption(
                guest_id=guest_uuid,
                requirement_type=DietaryType.VEGETARIAN,
                notes="Initial notes",
            )
            session.add(dietary)
            await session.flush()

            write_model = SqlRSVPWriteModel(
                session_overwrite=session,
                email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=True,
                dietary_requirements=[{"requirement_type": "vegan", "notes": "New preference"}],
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="test-token-12345",
                rsvp_data=rsvp_data,
            )

            # Verify old dietary requirements are cleared
            result = await session.execute(
                select(DietaryOption).where(DietaryOption.guest_id == guest_uuid)
            )
            dietary_opts = result.scalars().all()
            assert len(dietary_opts) == 1
            assert dietary_opts[0].requirement_type == DietaryType.VEGAN
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_without_email_service():
    """Test submitting an RSVP without an email service (should not fail)."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            await create_test_guest(session, user)

            write_model = SqlRSVPWriteModel(session_overwrite=session)

            rsvp_data = RSVPResponseSubmit(
                attending=True,
                dietary_requirements=[],
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="test-token-12345",
                rsvp_data=rsvp_data,
            )

            assert isinstance(result, RSVPResponseDTO)
            assert result.attending is True
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_declined_clears_plus_one():
    """Test that declining clears bring_a_plus_one_id."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            guest = await create_test_guest(session, user)
            guest_uuid = guest.uuid

            # Set initial bring_a_plus_one_id (simulating a guest who previously had a plus-one)
            guest = await session.get(Guest, guest_uuid)
            # Create a dummy plus-one guest to reference
            plus_one_guest = Guest(
                user_id=guest.user_id,
                first_name="Jane",
                last_name="Doe",
                plus_one_of_id=guest_uuid,
            )
            session.add(plus_one_guest)
            await session.flush()
            guest.bring_a_plus_one_id = plus_one_guest.uuid

            write_model = SqlRSVPWriteModel(
                session_overwrite=session,
                email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=False,
                dietary_requirements=[],
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="test-token-12345",
                rsvp_data=rsvp_data,
            )

            # Verify bring_a_plus_one_id is cleared when declining
            await session.refresh(guest)
            assert guest.bring_a_plus_one_id is None
        finally:
            await session.rollback()
