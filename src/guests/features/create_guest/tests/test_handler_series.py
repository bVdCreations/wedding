"""Tests for CreateGuestHandler - series command execution (Phase 3)."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import RSVPDTO, GuestDTO, GuestStatus, Language
from src.guests.features.create_guest.command import (
    CommandStatus,
    CreateGuestCommand,
    CreateGuestSeriesCommand,
    CreateGuestSeriesResult,
)
from src.guests.features.create_guest.handler import CreateGuestHandler
from src.guests.features.create_guest.write_model import (
    GuestCreateWriteModel,
    SqlGuestCreateWriteModel,
)
from src.guests.repository.orm_models import Guest
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


class TestExecuteSeries:
    """Tests for handler executing series of commands."""

    async def test_execute_series_all_success(self, session):
        """Test executing series where all commands succeed."""
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email=unique_email(), first_name="John", last_name="Doe"),
                CreateGuestCommand(email=unique_email(), first_name="Jane", last_name="Smith"),
                CreateGuestCommand(email=unique_email(), first_name="Bob", last_name="Wilson"),
            ]
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestSeriesResult)
        assert result.total == 3
        assert result.created == 3
        assert result.skipped == 0
        assert result.errors == 0
        assert result.emails_sent == 0
        assert result.emails_failed == 0
        assert len(result.results) == 3

        for r in result.results:
            assert r.status == CommandStatus.CREATED
            assert r.guest_id is not None

    async def test_execute_series_with_one_error(self, session):
        """Test executing series where one command fails - all should rollback."""

        class MockWriteModelAlwaysFails(GuestCreateWriteModel):
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
                raise RuntimeError("Simulated database error")

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=MockWriteModelAlwaysFails(),
        )
        email1 = unique_email()
        email2 = unique_email()
        email3 = unique_email()
        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email=email1, first_name="John", last_name="Doe"),
                CreateGuestCommand(email=email2, first_name="Jane", last_name="Smith"),
                CreateGuestCommand(email=email3, first_name="Bob", last_name="Wilson"),
            ]
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestSeriesResult)
        assert result.total == 3
        assert result.created == 0
        assert result.skipped == 0
        assert result.errors == 3

        for r in result.results:
            assert r.status == CommandStatus.ERROR

        users = await session.execute(select(User).where(User.email.in_([email1, email2, email3])))
        users = users.scalars().all()
        assert len(users) == 0

    async def test_execute_series_empty(self, session):
        """Test executing empty series."""
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestSeriesCommand(commands=[])

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestSeriesResult)
        assert result.total == 0
        assert result.created == 0
        assert result.skipped == 0
        assert result.errors == 0
        assert result.results == []

    async def test_execute_series_mixed_results(self, session):
        """Test executing series with mixed results (created and skipped)."""
        email1 = unique_email()
        email2 = unique_email()
        email3 = unique_email()

        user2 = User(
            uuid=uuid4(),
            email=email2,
            hashed_password=None,
            is_active=True,
            is_superuser=False,
        )
        session.add(user2)
        await session.flush()

        guest = Guest(
            user_id=user2.uuid,
            first_name="Existing",
            last_name="Guest",
            preferred_language="en",
        )
        session.add(guest)
        await session.flush()

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email=email1, first_name="John", last_name="Doe"),
                CreateGuestCommand(email=email2, first_name="Jane", last_name="Smith"),
                CreateGuestCommand(email=email3, first_name="Bob", last_name="Wilson"),
            ]
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestSeriesResult)
        assert result.total == 3
        assert result.created == 2
        assert result.skipped == 1
        assert result.errors == 0

        created_count = sum(1 for r in result.results if r.status == CommandStatus.CREATED)
        skipped_count = sum(1 for r in result.results if r.status == CommandStatus.SKIPPED)
        assert created_count == 2
        assert skipped_count == 1

    async def test_execute_series_rolls_back_on_error(self, session):
        """Test that series rolls back all changes when one fails."""

        call_count = [0]

        class MockWriteModelFailingAtSecond(GuestCreateWriteModel):
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
                call_count[0] += 1
                if call_count[0] == 2:
                    raise RuntimeError("Simulated database error on second guest")
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
            create_guest_write_model=MockWriteModelFailingAtSecond(),
        )
        email1 = unique_email()
        email2 = unique_email()
        email3 = unique_email()
        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email=email1, first_name="John", last_name="Doe"),
                CreateGuestCommand(email=email2, first_name="Jane", last_name="Smith"),
                CreateGuestCommand(email=email3, first_name="Bob", last_name="Wilson"),
            ]
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestSeriesResult)
        assert result.errors == 3

        users = await session.execute(select(User).where(User.email.in_([email1, email2, email3])))
        users = users.scalars().all()
        assert len(users) == 0

        guest_user_ids = [
            u.uuid
            for u in await session.execute(
                select(User.uuid).where(User.email.in_([email1, email2, email3]))
            )
        ]
        if guest_user_ids:
            guests = await session.execute(select(Guest).where(Guest.user_id.in_(guest_user_ids)))
            guests = guests.scalars().all()
            assert len(guests) == 0
        else:
            assert True

    async def test_execute_series_commits_only_on_all_success(self, session):
        """Test that series only commits when all commands succeed."""
        email1 = unique_email()
        email2 = unique_email()
        email3 = unique_email()

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email=email1, first_name="John", last_name="Doe"),
                CreateGuestCommand(email=email2, first_name="Jane", last_name="Smith"),
                CreateGuestCommand(email=email3, first_name="Bob", last_name="Wilson"),
            ]
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestSeriesResult)
        assert result.created == 3

        users = await session.execute(select(User).where(User.email.in_([email1, email2, email3])))
        users = users.scalars().all()
        assert len(users) == 3

        guests = await session.execute(
            select(Guest)
            .join(User, Guest.user_id == User.uuid)
            .where(User.email.in_([email1, email2, email3]))
        )
        guests = guests.scalars().all()
        assert len(guests) == 3
