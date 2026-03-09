"""Tests for ResendEmailService.send_invitation_for_guest."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from src.config.database import async_session_manager
from src.email_service.dtos import EmailStatus
from src.email_service.resend_service import ResendEmailService
from src.guests.dtos import GuestStatus, Language
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User


async def create_test_user(async_session, email=None):
    """Create a test user."""
    if email is None:
        email = f"test-{uuid4().hex[:8]}@example.com"
    user = User(email=email, hashed_password="hashed_password")
    async_session.add(user)
    await async_session.flush()
    await async_session.refresh(user)
    return user


async def create_test_guest_with_rsvp(async_session, test_user, rsvp_token=None):
    """Create a test guest with RSVP info."""
    if rsvp_token is None:
        rsvp_token = f"test-token-{uuid4().hex[:8]}"
    guest = Guest(
        user_id=test_user.uuid,
        first_name="John",
        last_name="Doe",
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
    return guest


class MockResendEmailService(ResendEmailService):
    """Mock that tracks calls and optionally raises exceptions."""

    def __init__(self, *args, **kwargs):
        super().__init__(config=MockConfig())
        self.send_invitation_called = False
        self.send_invitation_kwargs = {}
        self.raise_on_send = False

    def set_session_overwrite(self, session):
        self._session_overwrite = session

    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        rsvp_url: str,
        guest_id,
        language=None,
        user_id=None,
    ):
        self.send_invitation_called = True
        self.send_invitation_kwargs = {
            "to_address": to_address,
            "guest_name": guest_name,
            "rsvp_url": rsvp_url,
            "language": language,
            "guest_id": guest_id,
            "user_id": user_id,
        }
        if self.raise_on_send:
            raise Exception("Simulated send failure")


class MockConfig:
    resend_api_key = "test_key"
    emails_from = "test@example.com"


# ====== TEST CASES ======


@pytest.mark.asyncio
async def test_send_invitation_for_guest_success():
    """Test happy path: guest with user and rsvp info exists."""
    async with async_session_manager() as session:
        user = await create_test_user(session)
        guest = await create_test_guest_with_rsvp(session, user)
        await session.commit()

        service = MockResendEmailService()
        service.set_session_overwrite(session)

        result = await service.send_invitation_for_guest(guest_id=guest.uuid)

        assert result.status == EmailStatus.SENT
        assert service.send_invitation_called
        assert service.send_invitation_kwargs["to_address"] == user.email
        assert service.send_invitation_kwargs["guest_name"] == "John Doe"

        rsvp = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid))
        rsvp_info = rsvp.scalar_one()
        assert rsvp_info.email_sent_on is not None


@pytest.mark.asyncio
async def test_send_invitation_for_guest_guest_not_found():
    """Test when guest does not exist."""
    async with async_session_manager() as session:
        service = MockResendEmailService()
        service.set_session_overwrite(session)

        non_existent_guest_id = uuid4()
        result = await service.send_invitation_for_guest(guest_id=non_existent_guest_id)

        assert result.status == EmailStatus.FAILED
        assert "Guest not found" in (result.error or "")


@pytest.mark.asyncio
async def test_send_invitation_for_guest_rsvp_not_found():
    """Test when guest exists but RSVPInfo does not."""
    async with async_session_manager() as session:
        user = await create_test_user(session)

        guest = Guest(
            user_id=user.uuid,
            first_name="John",
            last_name="Doe",
            preferred_language=Language.EN,
        )
        session.add(guest)
        await session.flush()
        guest_uuid = guest.uuid
        await session.commit()

        service = MockResendEmailService()
        service.set_session_overwrite(session)
        result = await service.send_invitation_for_guest(guest_id=guest_uuid)

        assert result.status == EmailStatus.FAILED
        assert "RSVPInfo not found" in (result.error or "")
        rsvp = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid))
        rsvp_info = rsvp.scalar_one_or_none()
        assert rsvp_info is None


@pytest.mark.asyncio
async def test_send_invitation_for_guest_user_not_found():
    """Test when guest exists but user_id is None."""
    async with async_session_manager() as session:
        guest = Guest(
            user_id=None,
            first_name="John",
            last_name="Doe",
            preferred_language=Language.EN,
        )
        session.add(guest)
        await session.flush()
        guest_uuid = guest.uuid

        rsvp_info = RSVPInfo(
            guest_id=guest_uuid,
            status=GuestStatus.PENDING,
            rsvp_token=f"test-token-no-user-{uuid4().hex[:8]}",
            rsvp_link="http://example.com/rsvp/test",
        )
        session.add(rsvp_info)
        await session.commit()

        service = MockResendEmailService()
        service.set_session_overwrite(session)
        result = await service.send_invitation_for_guest(guest_id=guest_uuid)

        assert result.status == EmailStatus.FAILED
        assert "User not found" in (result.error or "")
        rsvp = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid))
        rsvp_info = rsvp.scalar_one()
        assert rsvp_info.email_sent_on is None


@pytest.mark.asyncio
async def test_send_invitation_for_guest_send_fails():
    """Test when send_invitation raises an exception."""
    async with async_session_manager() as session:
        user = await create_test_user(session)
        guest = await create_test_guest_with_rsvp(session, user)
        guest_uuid = guest.uuid
        await session.commit()

        service = MockResendEmailService()
        service.set_session_overwrite(session)
        service.raise_on_send = True

        result = await service.send_invitation_for_guest(guest_id=guest_uuid)

        assert result.status == EmailStatus.FAILED
        assert "Simulated send failure" in (result.error or "")

        rsvp = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_uuid))
        rsvp_info = rsvp.scalar_one()
        assert rsvp_info.email_sent_on is None


@pytest.mark.asyncio
async def test_send_invitation_for_guest_none_guest_id():
    """Test when guest_id is None."""
    async with async_session_manager() as session:
        service = MockResendEmailService()
        service.set_session_overwrite(session)

        result = await service.send_invitation_for_guest(guest_id=None)

        assert result.status == EmailStatus.FAILED
        assert "guest_id is None" in (result.error or "")


@pytest.mark.asyncio
async def test_email_type_accepts_any_string():
    """Test that email_type column accepts any string value (not restricted by enum).

    This test covers the bug where 'plus_one_invitation' was rejected because
    the enum only had 'plus_one_invite'. Now that email_type is a plain varchar,
    any string should be accepted.
    """
    from src.guests.repository.orm_models import EmailLog

    async with async_session_manager() as session:
        email_types_to_test = [
            "invitation",
            "confirmation",
            "reminder",
            "plus_one_invite",
            "plus_one_invitation",
            "forwarded",
            "rsvp_declined",
            "custom_email_type",
            "any_arbitrary_string_12345",
        ]

        for email_type in email_types_to_test:
            email_log = EmailLog(
                to_address="test@example.com",
                from_address="from@example.com",
                subject="Test Subject",
                html_body="<p>Test</p>",
                text_body="Test",
                email_type=email_type,
                status="pending",
            )
            session.add(email_log)
            await session.flush()
            await session.refresh(email_log)

            assert email_log.email_type == email_type
            assert email_log.uuid is not None

            session.expunge(email_log)

        await session.commit()
