"""Tests for SqlRSVPWriteModel."""

import pytest
from sqlalchemy import select

from src.config.database import async_session_manager
from src.email_service.base import EmailServiceBase
from src.guests.dtos import DietaryType, GuestStatus, Language, RSVPResponseDTO
from src.guests.features.update_rsvp.router import DietaryRequirement, RSVPResponseSubmit
from src.guests.repository.orm_models import DietaryOption, Guest, RSVPInfo
from src.guests.repository.write_models import SqlRSVPWriteModel
from src.models.user import User


class MockEmailService(EmailServiceBase):
    """Mock email service for testing."""

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
        language: Language = Language.EN,
        guest_id=None,
        user_id=None,
    ) -> None:
        """Mock send confirmation - does nothing."""
        pass

    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        event_date: str,
        event_location: str,
        rsvp_url: str,
        response_deadline: str,
        language: Language = Language.EN,
        guest_id=None,
        user_id=None,
    ) -> None:
        """Mock send invitation - does nothing."""
        pass

    async def send_invite_one_plus_one(
        self,
        to_address: str,
        guest_name: str,
        plus_one_details: dict,
        language: Language = Language.EN,
        guest_id=None,
        user_id=None,
    ) -> None:
        """Mock send invite one plus one - does nothing."""
        pass


async def create_test_user(async_session, email="test@example.com"):
    """Create a test user, cleaning up any existing test data first."""
    # Clean up existing test user if it exists
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
                session_overwrite=session, email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=True,
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
            rsvp_result = await session.execute(
                select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid)
            )
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
                session_overwrite=session, email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=False,
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
            rsvp_result = await session.execute(
                select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid)
            )
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
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    dietary_requirements=[
                        DietaryRequirement(requirement_type=DietaryType.VEGETARIAN, notes="No mushrooms please"),
                        DietaryRequirement(requirement_type=DietaryType.GLUTEN_FREE, notes=None),
                    ],
                ),
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
            _guest = await create_test_guest(session, user)

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            # Test that plus_one_details data is accepted (actual creation requires separate test)
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                plus_one_details=None,  # Set to None since we don't test full plus_one creation here
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
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    dietary_requirements=[DietaryRequirement(requirement_type=DietaryType.VEGAN, notes="New preference")],
                ),
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
            assert guest is not None
            # Create a dummy plus-one guest to reference
            plus_one_guest = Guest(
                user_id=guest.user_id,
                first_name="Jane",
                last_name="Doe",
                plus_one_of_id=guest_uuid,
                preferred_language=Language.EN,
            )
            session.add(plus_one_guest)
            await session.flush()
            guest.bring_a_plus_one_id = plus_one_guest.uuid

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            rsvp_data = RSVPResponseSubmit(
                attending=False,
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


# Language-specific tests


class SpyEmailService(EmailServiceBase):
    """Email service that captures calls for testing."""

    def __init__(self):
        self.send_confirmation_calls = []

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
        language: Language = Language.EN,
        guest_id=None,
        user_id=None,
    ) -> None:
        """Capture send confirmation calls."""
        self.send_confirmation_calls.append(
            {
                "to_address": to_address,
                "guest_name": guest_name,
                "attending": attending,
                "dietary": dietary,
                "language": language,
            }
        )

    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        event_date: str,
        event_location: str,
        rsvp_url: str,
        response_deadline: str,
        language: Language = Language.EN,
        guest_id=None,
        user_id=None,
    ) -> None:
        """Mock send invitation - does nothing."""
        pass

    async def send_invite_one_plus_one(
        self,
        to_address: str,
        guest_name: str,
        plus_one_details: dict,
        language: Language = Language.EN,
        guest_id=None,
        user_id=None,
    ) -> None:
        """Mock send invite one plus one - does nothing."""
        pass


async def create_test_guest_with_language(
    async_session, test_user, rsvp_token: str, language: Language
):
    """Create a test guest with RSVP info and specific language."""
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
        preferred_language=language,
    )
    async_session.add(guest)
    await async_session.flush()
    await async_session.refresh(guest)

    rsvp_info = RSVPInfo(
        guest_id=guest.uuid,
        status=GuestStatus.PENDING,
        rsvp_token=rsvp_token,
        rsvp_link=f"http://example.com/{language.value}/rsvp/{rsvp_token}",
    )
    async_session.add(rsvp_info)
    await async_session.flush()
    await async_session.refresh(guest)

    return guest


@pytest.mark.asyncio
async def test_submit_rsvp_sends_confirmation_email_in_spanish():
    """Test that RSVP confirmation email is sent in Spanish for Spanish guest."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="spanish_rsvp@example.com")
            _guest = await create_test_guest_with_language(
                session, user, "spanish-token-123", Language.ES
            )

            spy_email_service = SpyEmailService()
            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=spy_email_service
            )

            rsvp_data = RSVPResponseSubmit(
                attending=True,
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="spanish-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify email was sent with Spanish language
            assert len(spy_email_service.send_confirmation_calls) == 1
            call = spy_email_service.send_confirmation_calls[0]
            assert call["language"] == Language.ES
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_sends_confirmation_email_in_dutch():
    """Test that RSVP confirmation email is sent in Dutch for Dutch guest."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="dutch_rsvp@example.com")
            _guest = await create_test_guest_with_language(
                session, user, "dutch-token-123", Language.NL
            )

            spy_email_service = SpyEmailService()
            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=spy_email_service
            )

            rsvp_data = RSVPResponseSubmit(
                attending=True,
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="dutch-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify email was sent with Dutch language
            assert len(spy_email_service.send_confirmation_calls) == 1
            call = spy_email_service.send_confirmation_calls[0]
            assert call["language"] == Language.NL
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_sends_confirmation_email_in_english_by_default():
    """Test that RSVP confirmation email is sent in English for English guest."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="english_rsvp@example.com")
            _guest = await create_test_guest_with_language(
                session, user, "english-token-123", Language.EN
            )

            spy_email_service = SpyEmailService()
            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=spy_email_service
            )

            rsvp_data = RSVPResponseSubmit(
                attending=True,
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="english-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify email was sent with English language
            assert len(spy_email_service.send_confirmation_calls) == 1
            call = spy_email_service.send_confirmation_calls[0]
            assert call["language"] == Language.EN
        finally:
            await session.rollback()


# Allergies tests - High Priority


@pytest.mark.asyncio
async def test_submit_rsvp_saves_guest_allergies():
    """Test that guest allergies are saved when submitting RSVP with guest_info."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="allergies-token-123")
            guest_uuid = guest.uuid

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    allergies="Peanuts, shellfish, dairy",
                ),
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify RSVP was successful
            assert result.attending is True

            # Verify allergies were saved
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.allergies == "Peanuts, shellfish, dairy"
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_updates_existing_allergies():
    """Test that existing allergies are updated (not appended) when re-submitting RSVP."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="update_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="update-allergies-token-123")
            guest_uuid = guest.uuid

            # Set initial allergies
            guest.allergies = "Old allergies: gluten"
            await session.flush()

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    allergies="New allergies: peanuts, soy",
                ),
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="update-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify allergies were replaced, not appended
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.allergies == "New allergies: peanuts, soy"
            assert "Old allergies" not in updated_guest.allergies
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_saves_allergies_with_dietary():
    """Test that both allergies and dietary requirements are saved correctly."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="allergies_dietary@example.com")
            guest = await create_test_guest(session, user, rsvp_token="allergies-dietary-token-123")
            guest_uuid = guest.uuid

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    allergies="Severe peanut allergy",
                    dietary_requirements=[
                        DietaryRequirement(requirement_type=DietaryType.VEGETARIAN, notes="No eggs"),
                        DietaryRequirement(requirement_type=DietaryType.GLUTEN_FREE, notes=None),
                    ],
                ),
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="allergies-dietary-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify RSVP was successful
            assert result.attending is True

            # Verify allergies were saved
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.allergies == "Severe peanut allergy"

            # Verify dietary requirements were also saved
            dietary_result = await session.execute(
                select(DietaryOption).where(DietaryOption.guest_id == guest_uuid)
            )
            dietary_opts = dietary_result.scalars().all()
            assert len(dietary_opts) == 2
            assert any(d.requirement_type == DietaryType.VEGETARIAN for d in dietary_opts)
            assert any(d.requirement_type == DietaryType.GLUTEN_FREE for d in dietary_opts)
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_saves_plus_one_allergies():
    """Test that plus-one allergies are saved when creating a plus-one guest."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="plus_one_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="plus-one-allergies-token-123")
            guest_uuid = guest.uuid

            # Import and setup plus-one write model
            from src.guests.features.create_plus_one_guest.write_model import SqlPlusOneGuestWriteModel
            plus_one_write_model = SqlPlusOneGuestWriteModel()

            write_model = SqlRSVPWriteModel(
                session_overwrite=session,
                email_service=MockEmailService(),
                plus_one_guest_write_model=plus_one_write_model,
            )

            from src.guests.features.update_rsvp.router import PlusOneSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                plus_one_details=PlusOneSubmit(
                    email="plusone@example.com",
                    first_name="Jane",
                    last_name="Smith",
                    allergies="Lactose intolerant",
                    dietary_requirements=[],
                ),
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="plus-one-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify RSVP was successful
            assert result.attending is True

            # Verify primary guest has plus-one reference
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.bring_a_plus_one_id is not None

            # Verify plus-one guest has allergies saved
            plus_one_result = await session.execute(
                select(Guest).where(Guest.uuid == updated_guest.bring_a_plus_one_id)
            )
            plus_one_guest = plus_one_result.scalar_one()
            assert plus_one_guest.allergies == "Lactose intolerant"
            assert plus_one_guest.plus_one_of_id == guest_uuid
        finally:
            await session.rollback()


# Allergies tests - Medium Priority


@pytest.mark.asyncio
async def test_submit_rsvp_saves_family_member_allergies():
    """Test that family member allergies are saved via guest_info in family_member_updates."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="family_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="family-allergies-token-123")

            # Create a family member (without Family model to avoid test setup complexity)
            family_member = Guest(
                user_id=user.uuid,
                first_name="Child",
                last_name="Doe",
                preferred_language=Language.EN,
            )
            session.add(family_member)
            await session.flush()

            # Create RSVP info for family member
            family_member_rsvp = RSVPInfo(
                guest_id=family_member.uuid,
                status=GuestStatus.PENDING,
                rsvp_token="family-member-token",
                rsvp_link="http://example.com/rsvp/family-member-token",
            )
            session.add(family_member_rsvp)
            await session.flush()

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import FamilyMemberSubmit, GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                family_member_updates={
                    str(family_member.uuid): FamilyMemberSubmit(
                        attending=True,
                        guest_info=GuestInfoSubmit(
                            first_name="Child",
                            last_name="Doe",
                            allergies="Dairy allergy",
                            dietary_requirements=[],
                        ),
                    ),
                },
            )

            await write_model.submit_rsvp(
                token="family-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify family member allergies were saved
            family_member_result = await session.execute(
                select(Guest).where(Guest.uuid == family_member.uuid)
            )
            updated_family_member = family_member_result.scalar_one()
            assert updated_family_member.allergies == "Dairy allergy"
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_clears_allergies_with_empty_string():
    """Test that allergies can be cleared by submitting an empty string."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="clear_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="clear-allergies-token-123")
            guest_uuid = guest.uuid

            # Set initial allergies
            guest.allergies = "Old allergies to be cleared"
            await session.flush()

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    allergies="",  # Empty string to clear
                ),
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="clear-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify allergies were cleared
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.allergies == ""
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_allergies_persist_when_not_provided():
    """Test that allergies are not cleared when guest_info.allergies is None."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="persist_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="persist-allergies-token-123")
            guest_uuid = guest.uuid

            # Set initial allergies
            guest.allergies = "Existing allergies"
            await session.flush()

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    allergies=None,  # None should not clear existing allergies
                ),
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="persist-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify allergies persisted
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.allergies == "Existing allergies"
        finally:
            await session.rollback()


# Allergies tests - Low Priority


@pytest.mark.asyncio
async def test_submit_rsvp_long_allergies_text():
    """Test that long allergies text is handled correctly (stress test)."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="long_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="long-allergies-token-123")
            guest_uuid = guest.uuid

            # Create a long allergies string (500+ characters)
            long_allergies = "Allergies: " + ", ".join([f"allergen_{i}" for i in range(100)])
            assert len(long_allergies) > 500

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    allergies=long_allergies,
                ),
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="long-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify RSVP was successful
            assert result.attending is True

            # Verify long allergies were saved
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.allergies == long_allergies
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_special_characters_in_allergies():
    """Test that special characters, unicode, and newlines in allergies are handled correctly."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="special_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="special-allergies-token-123")
            guest_uuid = guest.uuid

            # Allergies with special characters, unicode, and newlines
            special_allergies = "Allergies:\n- Peanuts 🥜\n- Shellfish 🦐\n- Lactose (milk products)\n- Émoji test 😊"

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    allergies=special_allergies,
                ),
                family_member_updates={},
            )

            result = await write_model.submit_rsvp(
                token="special-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify RSVP was successful
            assert result.attending is True

            # Verify special characters in allergies were saved correctly
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.allergies == special_allergies
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_submit_rsvp_updates_phone_and_allergies():
    """Test that both phone and allergies fields are updated correctly together."""
    async with async_session_manager() as session:
        try:
            user = await create_test_user(session, email="phone_allergies@example.com")
            guest = await create_test_guest(session, user, rsvp_token="phone-allergies-token-123")
            guest_uuid = guest.uuid

            # Set initial values
            guest.phone = "+1234567890"
            guest.allergies = "Old allergies"
            await session.flush()

            write_model = SqlRSVPWriteModel(
                session_overwrite=session, email_service=MockEmailService()
            )

            from src.guests.features.update_rsvp.router import GuestInfoSubmit
            rsvp_data = RSVPResponseSubmit(
                attending=True,
                guest_info=GuestInfoSubmit(
                    first_name="John",
                    last_name="Doe",
                    phone="+9876543210",
                    allergies="New allergies: shellfish",
                ),
                family_member_updates={},
            )

            await write_model.submit_rsvp(
                token="phone-allergies-token-123",
                rsvp_data=rsvp_data,
            )

            # Verify both phone and allergies were updated
            guest_result = await session.execute(
                select(Guest).where(Guest.uuid == guest_uuid)
            )
            updated_guest = guest_result.scalar_one()
            assert updated_guest.phone == "+9876543210"
            assert updated_guest.allergies == "New allergies: shellfish"
        finally:
            await session.rollback()
