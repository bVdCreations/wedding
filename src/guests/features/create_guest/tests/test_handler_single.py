"""Tests for CreateGuestHandler - single command execution."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from src.config.database import async_session_maker
from src.guests.dtos import GuestDTO, Language
from src.guests.features.create_guest.command import (
    CommandStatus,
    CreateGuestCommand,
    CreateGuestCommandResult,
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


class TestExecuteSingleCommand:
    """Tests for handler executing single command."""

    async def test_execute_single_new_user(self, session):
        """Test creating a guest with a new user."""
        email = unique_email()
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestCommand(
            email=email,
            first_name="John",
            last_name="Doe",
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestCommandResult)
        assert result.status is not None
        assert result.status == CommandStatus.CREATED
        assert result.guest_id is not None
        assert "created" in result.message.lower()

        db_user = await session.execute(select(User).where(User.email == email))
        db_user = db_user.scalar_one_or_none()
        assert db_user is not None
        assert db_user.email == email

        db_guest = await session.execute(select(Guest).where(Guest.uuid == result.guest_id))
        db_guest = db_guest.scalar_one_or_none()
        assert db_guest is not None
        assert db_guest.first_name == "John"
        assert db_guest.last_name == "Doe"

    async def test_execute_single_existing_user_no_guest(self, session):
        """Test creating guest when user exists but has no guest."""
        email = unique_email()
        user = User(
            uuid=uuid4(),
            email=email,
            hashed_password=None,
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestCommand(
            email=email,
            first_name="Jane",
            last_name="Smith",
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestCommandResult)
        assert result.status == CommandStatus.CREATED
        assert result.email == email
        assert result.guest_id is not None

        db_user = await session.execute(select(User).where(User.email == email))
        db_user = db_user.scalar_one_or_none()
        assert db_user is not None

        db_guest = await session.execute(select(Guest).where(Guest.uuid == result.guest_id))
        db_guest = db_guest.scalar_one_or_none()
        assert db_guest is not None
        assert db_guest.first_name == "Jane"
        assert db_guest.last_name == "Smith"

    async def test_execute_single_existing_user_with_guest(self, session):
        """Test creating guest when user already has a guest (lookup by email)."""
        email = unique_email()
        user = User(
            uuid=uuid4(),
            email=email,
            hashed_password=None,
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()

        guest = Guest(
            user_id=user.uuid,
            first_name="John",
            last_name="Doe",
            preferred_language="en",
        )
        session.add(guest)
        await session.flush()

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestCommand(
            email=email,
            first_name="Another",
            last_name="Guest",
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestCommandResult)
        assert result.status == CommandStatus.SKIPPED
        assert "already has a guest" in result.message.lower()

        db_user = await session.execute(select(User).where(User.email == email))
        db_user = db_user.scalar_one_or_none()
        assert db_user is not None

        db_guests = await session.execute(select(Guest).where(Guest.user_id == db_user.uuid))
        db_guests = db_guests.scalars().all()
        assert len(db_guests) == 1
        assert db_guests[0].first_name == "John"

    async def test_execute_single_with_language(self, session):
        """Test creating guest with specific language."""
        email = unique_email()
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestCommand(
            email=email,
            first_name="Juan",
            last_name="Perez",
            lang="es",
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestCommandResult)
        assert result.status == CommandStatus.CREATED

        db_user = await session.execute(select(User).where(User.email == email))
        db_user = db_user.scalar_one_or_none()
        assert db_user is not None

        db_guest = await session.execute(select(Guest).where(Guest.user_id == db_user.uuid))
        db_guest = db_guest.scalar_one_or_none()
        assert db_guest is not None
        assert db_guest.preferred_language == "es"

    async def test_execute_single_with_empty_names(self, session):
        """Test creating guest with empty first/last name."""
        email = unique_email()
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestCommand(
            email=email,
            first_name="",
            last_name="",
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestCommandResult)
        assert result.status == CommandStatus.CREATED

        db_user = await session.execute(select(User).where(User.email == email))
        db_user = db_user.scalar_one_or_none()
        assert db_user is not None

        db_guest = await session.execute(select(Guest).where(Guest.user_id == db_user.uuid))
        db_guest = db_guest.scalar_one_or_none()
        assert db_guest is not None
        assert db_guest.first_name == ""
        assert db_guest.last_name == ""


class TestErrorHandling:
    """Tests for error handling in CreateGuestHandler."""

    async def test_execute_handles_generic_exception(self, session):
        """Test that generic exceptions are caught and return ERROR status."""

        class MockWriteModel(GuestCreateWriteModel):
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
                raise RuntimeError("Database connection failed")

        email = unique_email()
        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=MockWriteModel(),
        )

        command = CreateGuestCommand(
            email=email,
            first_name="John",
            last_name="Doe",
        )

        result = await handler.execute(command)

        assert isinstance(result, CreateGuestCommandResult)
        assert result.status == CommandStatus.ERROR
        assert result.email == email
        assert "Database connection failed" in result.message

    async def test_execute_series_not_implemented(self, session):
        """Test that series commands raise NotImplementedError."""
        from src.guests.features.create_guest.command import CreateGuestSeriesCommand

        handler = CreateGuestHandler(
            session_overwrite=session,
            create_guest_write_model=SqlGuestCreateWriteModel(session_overwrite=session),
        )
        command = CreateGuestSeriesCommand(
            commands=[
                CreateGuestCommand(email="test1@example.com", first_name="John", last_name="Doe"),
                CreateGuestCommand(email="test2@example.com", first_name="Jane", last_name="Smith"),
            ]
        )

        with pytest.raises(NotImplementedError):
            await handler.execute(command)
