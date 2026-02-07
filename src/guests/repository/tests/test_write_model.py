"""Tests for SqlRSVPWriteModel."""

import pytest
import pytest_asyncio
from sqlalchemy import select

from src.config.database import async_session_manager
from src.email.service import EmailService
from src.guests.dtos import DietaryType, GuestStatus, PlusOneDTO, RSVPResponseDTO
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


async def create_test_user(async_session):
    """Create a test user, cleaning up any existing test data first."""
    # Clean up existing test user if it exists
    existing_user = await async_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    if existing_user.scalar_one_or_none():
        await async_session.execute(select(User).where(User.email == "test@example.com"))
        await async_session.execute(User.__table__.delete().where(User.email == "test@example.com"))
        await async_session.commit()

    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


async def create_test_guest(async_session, test_user):
    """Create a test guest with RSVP info, cleaning up existing guest first."""
    # Clean up existing guest with same token if it exists
    existing_rsvp = await async_session.execute(
        select(RSVPInfo).where(RSVPInfo.rsvp_token == "test-token-12345")
    )
    existing_rsvp_data = existing_rsvp.scalar_one_or_none()
    if existing_rsvp_data:
        await async_session.execute(
            DietaryOption.__table__.delete().where(
                DietaryOption.guest_id == existing_rsvp_data.guest_id
            )
        )
        await async_session.execute(
            RSVPInfo.__table__.delete().where(RSVPInfo.rsvp_token == "test-token-12345")
        )
        await async_session.execute(
            Guest.__table__.delete().where(Guest.uuid == existing_rsvp_data.guest_id)
        )
        await async_session.commit()

    guest = Guest(
        user_id=test_user.uuid,
        first_name="John",
        last_name="Doe",
        phone="+1234567890",
    )
    async_session.add(guest)
    await async_session.commit()
    await async_session.refresh(guest)

    rsvp_info = RSVPInfo(
        guest_id=guest.uuid,
        status=GuestStatus.PENDING,
        rsvp_token="test-token-12345",
        rsvp_link="http://example.com/rsvp/test-token-12345",
    )
    async_session.add(rsvp_info)
    await async_session.commit()
    await async_session.refresh(guest)

    return guest


@pytest_asyncio.fixture
async def setup_test_data():
    """Set up test data for each test."""
    async with async_session_manager() as session:
        user = await create_test_user(session)
        guest = await create_test_guest(session, user)
        yield {"user": user, "guest": guest}

        # Cleanup after tests
        await session.execute(
            RSVPInfo.__table__.delete().where(RSVPInfo.rsvp_token == "test-token-12345")
        )
        await session.execute(Guest.__table__.delete().where(Guest.uuid == guest.uuid))
        await session.execute(User.__table__.delete().where(User.email == "test@example.com"))
        await session.commit()


@pytest.mark.asyncio
async def test_submit_rsvp_attending(setup_test_data):
    """Test submitting an RSVP with attending=true."""
    guest_uuid = setup_test_data["guest"].uuid

    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    result = await write_model.submit_rsvp(
        token="test-token-12345",
        attending=True,
        plus_one_details=None,
        dietary_requirements=[],
    )

    assert isinstance(result, RSVPResponseDTO)
    assert result.attending is True
    assert result.status == GuestStatus.CONFIRMED
    assert "Thank you for confirming" in result.message

    # Verify database state
    async with async_session_manager() as session:
        rsvp_result = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid))
        rsvp_info = rsvp_result.scalar_one()
        assert rsvp_info.status == GuestStatus.CONFIRMED


@pytest.mark.asyncio
async def test_submit_rsvp_not_attending(setup_test_data):
    """Test submitting an RSVP with attending=false."""
    guest_uuid = setup_test_data["guest"].uuid

    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    result = await write_model.submit_rsvp(
        token="test-token-12345",
        attending=False,
        plus_one_details=None,
        dietary_requirements=[],
    )

    assert isinstance(result, RSVPResponseDTO)
    assert result.attending is False
    assert result.status == GuestStatus.DECLINED
    assert "We're sorry you can't make it" in result.message

    # Verify database state
    async with async_session_manager() as session:
        rsvp_result = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid))
        rsvp_info = rsvp_result.scalar_one()
        assert rsvp_info.status == GuestStatus.DECLINED


@pytest.mark.asyncio
async def test_submit_rsvp_with_dietary_requirements(setup_test_data):
    """Test submitting an RSVP with dietary requirements."""
    guest_uuid = setup_test_data["guest"].uuid

    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    dietary_requirements = [
        {"requirement_type": "vegetarian", "notes": "No mushrooms please"},
        {"requirement_type": "gluten_free", "notes": None},
    ]

    result = await write_model.submit_rsvp(
        token="test-token-12345",
        attending=True,
        plus_one_details=None,
        dietary_requirements=dietary_requirements,
    )

    assert isinstance(result, RSVPResponseDTO)
    assert result.attending is True
    assert result.status == GuestStatus.CONFIRMED

    # Verify database state
    async with async_session_manager() as session:
        result = await session.execute(
            select(DietaryOption).where(DietaryOption.guest_id == guest_uuid)
        )
        dietary_opts = result.scalars().all()
        assert len(dietary_opts) == 2


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one(setup_test_data):
    """Test submitting an RSVP with plus one."""
    guest_uuid = setup_test_data["guest"].uuid

    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    plus_one_details = PlusOneDTO(
        email="jane@example.com",
        first_name="Jane",
        last_name="Doe",
    )

    result = await write_model.submit_rsvp(
        token="test-token-12345",
        attending=True,
        plus_one_details=plus_one_details,
        dietary_requirements=[],
    )

    assert isinstance(result, RSVPResponseDTO)
    assert result.attending is True

    # Verify database state - plus_one_name should be set for display
    async with async_session_manager() as session:
        guest = await session.get(Guest, guest_uuid)
        assert guest.plus_one_name == "Jane Doe"


@pytest.mark.asyncio
async def test_submit_rsvp_with_invalid_token():
    """Test submitting an RSVP with an invalid token."""
    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    with pytest.raises(ValueError, match="Invalid RSVP token"):
        await write_model.submit_rsvp(
            token="invalid-token",
            attending=True,
            plus_one_details=None,
            dietary_requirements=[],
        )


@pytest.mark.asyncio
async def test_submit_rsvp_clears_previous_dietary(setup_test_data):
    """Test that submitting an RSVP clears previous dietary requirements."""
    guest_uuid = setup_test_data["guest"].uuid

    # Add initial dietary requirement
    async with async_session_manager() as session:
        dietary = DietaryOption(
            guest_id=guest_uuid,
            requirement_type=DietaryType.VEGETARIAN,
            notes="Initial notes",
        )
        session.add(dietary)
        await session.commit()

    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    await write_model.submit_rsvp(
        token="test-token-12345",
        attending=True,
        plus_one_details=None,
        dietary_requirements=[{"requirement_type": "vegan", "notes": "New preference"}],
    )

    # Verify old dietary requirements are cleared
    async with async_session_manager() as session:
        result = await session.execute(
            select(DietaryOption).where(DietaryOption.guest_id == guest_uuid)
        )
        dietary_opts = result.scalars().all()
        assert len(dietary_opts) == 1
        assert dietary_opts[0].requirement_type == DietaryType.VEGAN


@pytest.mark.asyncio
async def test_submit_rsvp_without_email_service(setup_test_data):
    """Test submitting an RSVP without an email service (should not fail)."""
    write_model = SqlRSVPWriteModel(email_service=None)

    result = await write_model.submit_rsvp(
        token="test-token-12345",
        attending=True,
        plus_one_details=None,
        dietary_requirements=[],
    )

    assert isinstance(result, RSVPResponseDTO)
    assert result.attending is True


@pytest.mark.asyncio
async def test_submit_rsvp_declined_clears_plus_one(setup_test_data):
    """Test that declining clears plus one name."""
    guest_uuid = setup_test_data["guest"].uuid

    # Set initial plus one name
    async with async_session_manager() as session:
        guest = await session.get(Guest, guest_uuid)
        guest.plus_one_name = "Jane Doe"
        await session.commit()

    write_model = SqlRSVPWriteModel(email_service=MockEmailService())

    await write_model.submit_rsvp(
        token="test-token-12345",
        attending=False,
        plus_one_details=None,
        dietary_requirements=[],
    )

    # Verify plus one name is cleared when declining
    async with async_session_manager() as session:
        guest = await session.get(Guest, guest_uuid)
        assert guest.plus_one_name is None
