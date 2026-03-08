"""Tests for CreateGuestHandler - Two-phase execution (Phase 4)."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.email_service.base import EmailServiceBase
from src.email_service.dtos import EmailResult, EmailStatus
from src.guests.dtos import RSVPDTO, GuestDTO, GuestStatus, Language
from src.guests.features.create_guest.command import (
    CreateGuestCommand,
    CreateGuestSeriesCommand,
)
from src.guests.features.create_guest.handler import CreateGuestHandler
from src.guests.features.create_guest.write_model import (
    GuestCreateWriteModel,
    SqlGuestCreateWriteModel,
)
from src.models.user import User


def unique_email():
    """Generate unique email for test isolation."""
    return f"test-{uuid4().hex[:8]}@example.com"


@pytest.fixture
async def session():
    """Create a session for tests."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


class TestTwoPhaseExecution:
    """Tests for two-phase execution (Phase 1 + Phase 2)."""

    class MockEmailService(EmailServiceBase):
        async def send_invitation(
            self,
            to_address,
            guest_name,
            rsvp_url,
            language=None,
            guest_id=None,
            user_id=None,
        ):
            pass

        async def send_confirmation(
            self,
            to_address,
            guest_name,
            attending,
            dietary,
            language=None,
            guest_id=None,
            user_id=None,
        ):
            pass

        async def send_invite_one_plus_one(
            self,
            to_address,
            guest_name,
            inviter_name,
            rsvp_url,
            language=None,
            guest_id=None,
            user_id=None,
        ):
            pass

        async def send_invitation_for_guest(self, guest_id):
            return EmailResult(status=EmailStatus.SENT)

    async def test_phase1_success_phase2_send_emails(self, session):
        """Test that emails are sent when send_email=True."""
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
            email_service=TestTwoPhaseExecution.MockEmailService(),
        )

        email1 = unique_email()
        email2 = unique_email()
        email3 = unique_email()

        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(
                    email=email1, first_name="John", last_name="Doe", send_email=True
                ),
                CreateGuestCommand(
                    email=email2, first_name="Jane", last_name="Smith", send_email=True
                ),
                CreateGuestCommand(
                    email=email3, first_name="Bob", last_name="Wilson", send_email=True
                ),
            ]
        )

        result = await handler.execute(command)

        assert result.total == 3
        assert result.created == 3
        assert result.emails_sent == 3
        assert result.emails_failed == 0

        for r in result.results:
            assert r.email_status == "sent"
            assert r.email_error is None

    async def test_phase1_success_phase2_partial_failure(self, session):
        """Test partial email failure - some succeed, some fail."""

        call_count = [0]

        class MockEmailServiceFailingOnSecond(EmailServiceBase):
            async def send_invitation(
                self,
                to_address,
                guest_name,
                rsvp_url,
                language=None,
                guest_id=None,
                user_id=None,
            ):
                call_count[0] += 1
                if call_count[0] == 2:
                    raise RuntimeError("Simulated email failure")

            async def send_confirmation(
                self,
                to_address,
                guest_name,
                attending,
                dietary,
                language=None,
                guest_id=None,
                user_id=None,
            ):
                pass

            async def send_invite_one_plus_one(
                self,
                to_address,
                guest_name,
                inviter_name,
                rsvp_url,
                language=None,
                guest_id=None,
                user_id=None,
            ):
                pass

            async def send_invitation_for_guest(self, guest_id):
                call_count[0] += 1
                if call_count[0] == 2:
                    return EmailResult(status=EmailStatus.FAILED, error="Simulated email failure")
                return EmailResult(status=EmailStatus.SENT)

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
            email_service=MockEmailServiceFailingOnSecond(),
        )

        email1 = unique_email()
        email2 = unique_email()
        email3 = unique_email()

        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(
                    email=email1, first_name="John", last_name="Doe", send_email=True
                ),
                CreateGuestCommand(
                    email=email2, first_name="Jane", last_name="Smith", send_email=True
                ),
                CreateGuestCommand(
                    email=email3, first_name="Bob", last_name="Wilson", send_email=True
                ),
            ]
        )

        result = await handler.execute(command)

        assert result.total == 3
        assert result.created == 3
        assert result.emails_sent == 2
        assert result.emails_failed == 1

        results_with_email = [r for r in result.results if r.email_status is not None]
        sent_count = sum(1 for r in results_with_email if r.email_status == "sent")
        failed_count = sum(1 for r in results_with_email if r.email_status == "failed")
        assert sent_count == 2
        assert failed_count == 1

    async def test_phase1_success_phase2_no_emails(self, session):
        """Test that no emails are sent when send_email=False."""
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
            email_service=TestTwoPhaseExecution.MockEmailService(),
        )

        email1 = unique_email()
        email2 = unique_email()

        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email=email1, first_name="John", last_name="Doe"),
                CreateGuestCommand(email=email2, first_name="Jane", last_name="Smith"),
            ]
        )

        result = await handler.execute(command)

        assert result.total == 2
        assert result.created == 2
        assert result.emails_sent == 0
        assert result.emails_failed == 0

        for r in result.results:
            assert r.email_status is None
            assert r.email_error is None

    async def test_phase1_failure_rollback(self, session):
        """Test that Phase 2 doesn't run when Phase 1 fails."""

        class MockWriteModelFailingOnSecond(GuestCreateWriteModel):
            call_count = 0

            async def create_guest(
                self,
                email: str,
                first_name: str | None = None,
                last_name: str | None = None,
                phone: str | None = None,
                notes: str | None = None,
                send_email: bool = True,
                preferred_language: Language = Language.EN,
            ) -> GuestDTO:
                MockWriteModelFailingOnSecond.call_count += 1
                if MockWriteModelFailingOnSecond.call_count == 2:
                    raise RuntimeError("Simulated database error")
                return GuestDTO(
                    id=uuid4(),
                    email=email,
                    rsvp=RSVPDTO(
                        token="test",
                        link="http://test.com",
                        status=GuestStatus.PENDING,
                    ),
                )

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=MockWriteModelFailingOnSecond(),
            email_service=TestTwoPhaseExecution.MockEmailService(),
        )

        email1 = unique_email()
        email2 = unique_email()

        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email=email1, first_name="John", last_name="Doe"),
                CreateGuestCommand(email=email2, first_name="Jane", last_name="Smith"),
            ]
        )

        result = await handler.execute(command)

        assert result.total == 2
        assert result.created == 0
        assert result.errors == 2
        assert result.emails_sent == 0
        assert result.emails_failed == 0

        users = await session.execute(select(User).where(User.email.in_([email1, email2])))
        users = users.scalars().all()
        assert len(users) == 0

    async def test_phase2_exception_keeps_phase1(self, session):
        """Test that Phase 2 exceptions don't rollback Phase 1 committed guests."""

        class MockEmailServiceAlwaysFails(EmailServiceBase):
            async def send_invitation(
                self,
                to_address,
                guest_name,
                rsvp_url,
                language=None,
                guest_id=None,
                user_id=None,
            ):
                raise RuntimeError("Email service down")

            async def send_confirmation(
                self,
                to_address,
                guest_name,
                attending,
                dietary,
                language=None,
                guest_id=None,
                user_id=None,
            ):
                pass

            async def send_invite_one_plus_one(
                self,
                to_address,
                guest_name,
                inviter_name,
                rsvp_url,
                language=None,
                guest_id=None,
                user_id=None,
            ):
                pass

            async def send_invitation_for_guest(self, guest_id):
                return EmailResult(status=EmailStatus.FAILED, error="Email service down")

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
            email_service=MockEmailServiceAlwaysFails(),
        )

        email1 = unique_email()
        email2 = unique_email()

        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(
                    email=email1, first_name="John", last_name="Doe", send_email=True
                ),
                CreateGuestCommand(
                    email=email2, first_name="Jane", last_name="Smith", send_email=True
                ),
            ]
        )

        result = await handler.execute(command)

        assert result.total == 2
        assert result.created == 2
        assert result.errors == 0
        assert result.emails_sent == 0
        assert result.emails_failed == 2

        users = await session.execute(select(User).where(User.email.in_([email1, email2])))
        users = users.scalars().all()
        assert len(users) == 2
