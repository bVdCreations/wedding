"""Tests for SqlRSVPReadModel."""

import pytest
from sqlalchemy import select

from src.config.database import async_session_manager
from src.guests.dtos import DietaryType, GuestStatus, GuestType, Language
from src.guests.repository.orm_models import DietaryOption, Guest, RSVPInfo
from src.guests.repository.read_models import SqlRSVPReadModel
from src.models.user import User


async def create_test_user(async_session, email="test_read@example.com"):
    """Create a test user, cleaning up any existing test data first."""
    existing_user = await async_session.execute(select(User).where(User.email == email))
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


async def create_test_guest_with_uppercase_dietary(
    async_session, test_user, rsvp_token="test-bad-dietary-token"
):
    """Create a test guest with RSVP info and a dietary option containing uppercase value."""
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
        first_name="Jane",
        last_name="Smith",
        phone="+9876543210",
        preferred_language=Language.EN,
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

    dietary_option = DietaryOption(
        guest_id=guest.uuid,
        requirement_type="VEGETARIAN",
        notes="No meat",
    )
    async_session.add(dietary_option)
    await async_session.flush()

    return guest


@pytest.mark.asyncio
async def test_get_rsvp_info_with_uppercase_dietary_type():
    """Test that get_rsvp_info handles uppercase dietary type values (case-insensitive)."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            await create_test_guest_with_uppercase_dietary(session, user)
            await session.commit()

            read_model = SqlRSVPReadModel()

            result = await read_model.get_rsvp_info(token="test-bad-dietary-token")

            assert result is not None
            assert len(result.dietary_requirements) == 1
            assert result.dietary_requirements[0].requirement_type == DietaryType.VEGETARIAN
            assert result.dietary_requirements[0].notes == "No meat"
        finally:
            await session.rollback()


async def create_test_guest_with_uppercase_status(
    async_session, test_user, rsvp_token="test-uppercase-status-token"
):
    """Create a test guest with RSVP info containing uppercase status value."""
    existing_rsvp = await async_session.execute(
        select(RSVPInfo).where(RSVPInfo.rsvp_token == rsvp_token)
    )
    existing_rsvp_data = existing_rsvp.scalar_one_or_none()
    if existing_rsvp_data:
        await async_session.execute(
            RSVPInfo.__table__.delete().where(RSVPInfo.rsvp_token == rsvp_token)
        )
        await async_session.execute(
            Guest.__table__.delete().where(Guest.uuid == existing_rsvp_data.guest_id)
        )
        await async_session.flush()

    guest = Guest(
        user_id=test_user.uuid,
        first_name="Bob",
        last_name="Jones",
        phone="+1111111111",
        preferred_language=Language.EN,
    )
    async_session.add(guest)
    await async_session.flush()
    await async_session.refresh(guest)

    rsvp_info = RSVPInfo(
        guest_id=guest.uuid,
        status="CONFIRMED",
        rsvp_token=rsvp_token,
        rsvp_link=f"http://example.com/rsvp/{rsvp_token}",
    )
    async_session.add(rsvp_info)
    await async_session.flush()

    return guest


@pytest.mark.asyncio
async def test_get_rsvp_info_with_uppercase_guest_status():
    """Test that get_rsvp_info handles uppercase guest status values (case-insensitive)."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            await create_test_guest_with_uppercase_status(session, user)
            await session.commit()

            read_model = SqlRSVPReadModel()

            result = await read_model.get_rsvp_info(token="test-uppercase-status-token")

            assert result is not None
            assert result.status == GuestStatus.CONFIRMED
        finally:
            await session.rollback()


async def create_test_guest_with_uppercase_language(
    async_session, test_user, rsvp_token="test-uppercase-language-token"
):
    """Create a test guest with uppercase preferred language value."""
    existing_rsvp = await async_session.execute(
        select(RSVPInfo).where(RSVPInfo.rsvp_token == rsvp_token)
    )
    existing_rsvp_data = existing_rsvp.scalar_one_or_none()
    if existing_rsvp_data:
        await async_session.execute(
            RSVPInfo.__table__.delete().where(RSVPInfo.rsvp_token == rsvp_token)
        )
        await async_session.execute(
            Guest.__table__.delete().where(Guest.uuid == existing_rsvp_data.guest_id)
        )
        await async_session.flush()

    guest = Guest(
        user_id=test_user.uuid,
        first_name="Charlie",
        last_name="Brown",
        phone="+2222222222",
        preferred_language="ES",
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

    return guest


@pytest.mark.asyncio
async def test_get_rsvp_info_with_uppercase_language():
    """Test that get_rsvp_info handles uppercase preferred language values (case-insensitive)."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session)
            await create_test_guest_with_uppercase_language(session, user)
            await session.commit()

            read_model = SqlRSVPReadModel()

            result = await read_model.get_rsvp_info(token="test-uppercase-language-token")

            assert result is not None
            assert result.first_name == "Charlie"
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_dietary_type_case_insensitive_direct():
    """Test DietaryType enum directly with various case variants."""
    assert DietaryType("vegetarian") == DietaryType.VEGETARIAN
    assert DietaryType("VEGETARIAN") == DietaryType.VEGETARIAN
    assert DietaryType("Vegetarian") == DietaryType.VEGETARIAN
    assert DietaryType("VEGAN") == DietaryType.VEGAN
    assert DietaryType("vegan") == DietaryType.VEGAN


@pytest.mark.asyncio
async def test_guest_status_case_insensitive_direct():
    """Test GuestStatus enum directly with various case variants."""
    assert GuestStatus("pending") == GuestStatus.PENDING
    assert GuestStatus("PENDING") == GuestStatus.PENDING
    assert GuestStatus("Pending") == GuestStatus.PENDING
    assert GuestStatus("CONFIRMED") == GuestStatus.CONFIRMED
    assert GuestStatus("confirmed") == GuestStatus.CONFIRMED


@pytest.mark.asyncio
async def test_guest_type_case_insensitive_direct():
    """Test GuestType enum directly with various case variants."""
    assert GuestType("adult") == GuestType.ADULT
    assert GuestType("ADULT") == GuestType.ADULT
    assert GuestType("Adult") == GuestType.ADULT
    assert GuestType("CHILD") == GuestType.CHILD
    assert GuestType("child") == GuestType.CHILD


@pytest.mark.asyncio
async def test_language_case_insensitive_direct():
    """Test Language enum directly with various case variants."""
    assert Language("en") == Language.EN
    assert Language("EN") == Language.EN
    assert Language("En") == Language.EN
    assert Language("ES") == Language.ES
    assert Language("es") == Language.ES
    assert Language("NL") == Language.NL
    assert Language("nl") == Language.NL
