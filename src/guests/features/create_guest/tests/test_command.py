"""Tests for CreateGuestFactory and command classes."""

import pytest
from uuid import uuid4

from src.guests.features.create_guest.command import (
    CommandStatus,
    CreateGuestCommand,
    CreateGuestCommandResult,
    CreateGuestFactory,
    CreateGuestSeriesCommand,
    CreateGuestSeriesResult,
)


class TestCreateGuestCommand:
    """Tests for CreateGuestCommand dataclass."""

    def test_create_command_with_all_fields(self):
        """Test creating command with all fields."""
        user_id = uuid4()
        cmd = CreateGuestCommand(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            lang="en",
            user_id=user_id,
            send_email=True,
        )

        assert cmd.email == "test@example.com"
        assert cmd.first_name == "John"
        assert cmd.last_name == "Doe"
        assert cmd.lang == "en"
        assert cmd.user_id == user_id
        assert cmd.send_email is True

    def test_create_command_with_defaults(self):
        """Test creating command with only required field."""
        cmd = CreateGuestCommand(email="test@example.com")

        assert cmd.email == "test@example.com"
        assert cmd.first_name == ""
        assert cmd.last_name == ""
        assert cmd.lang == "en"
        assert cmd.user_id is None
        assert cmd.send_email is False


class TestCreateGuestCommandResult:
    """Tests for CreateGuestCommandResult dataclass."""

    def test_create_result_created(self):
        """Test creating a successful result."""
        guest_id = uuid4()
        result = CreateGuestCommandResult(
            status=CommandStatus.CREATED,
            email="test@example.com",
            message="Guest created",
            guest_id=guest_id,
        )

        assert result.status == CommandStatus.CREATED
        assert result.email == "test@example.com"
        assert result.message == "Guest created"
        assert result.guest_id == guest_id
        assert result.email_status is None

    def test_create_result_with_email_status(self):
        """Test creating result with email status."""
        result = CreateGuestCommandResult(
            status=CommandStatus.CREATED,
            email="test@example.com",
            message="Guest created",
            email_status="sent",
            email_error=None,
        )

        assert result.email_status == "sent"
        assert result.email_error is None


class TestCreateGuestSeriesCommand:
    """Tests for CreateGuestSeriesCommand dataclass."""

    def test_create_empty_series(self):
        """Test creating empty series."""
        series = CreateGuestSeriesCommand()

        assert series.commands == []

    def test_create_series_with_commands(self):
        """Test creating series with commands."""
        cmd1 = CreateGuestCommand(email="a@test.com")
        cmd2 = CreateGuestCommand(email="b@test.com")
        series = CreateGuestSeriesCommand(commands=[cmd1, cmd2])

        assert len(series.commands) == 2


class TestCreateGuestSeriesResult:
    """Tests for CreateGuestSeriesResult dataclass."""

    def test_create_result_with_counts(self):
        """Test creating series result with counts."""
        result = CreateGuestSeriesResult(
            total=5,
            created=3,
            skipped=1,
            errors=1,
            emails_sent=2,
            emails_failed=0,
        )

        assert result.total == 5
        assert result.created == 3
        assert result.skipped == 1
        assert result.errors == 1
        assert result.emails_sent == 2
        assert result.emails_failed == 0


class TestCreateGuestFactory:
    """Tests for CreateGuestFactory."""

    def test_create_commands_with_valid_rows(self):
        """Test creating commands from valid CSV rows."""
        rows = [
            {"email": "john@example.com", "first_name": "John", "last_name": "Doe", "lang": "en"},
            {"email": "jane@example.com", "first_name": "Jane", "last_name": "Smith", "lang": "es"},
        ]

        series = CreateGuestFactory.create_commands(rows)

        assert len(series.commands) == 2
        assert series.commands[0].email == "john@example.com"
        assert series.commands[0].first_name == "John"
        assert series.commands[0].last_name == "Doe"
        assert series.commands[0].lang == "en"
        assert series.commands[1].email == "jane@example.com"
        assert series.commands[1].lang == "es"

    def test_create_commands_with_empty_email(self):
        """Test that empty email raises ValueError."""
        rows = [
            {"email": "", "first_name": "John", "last_name": "Doe"},
        ]

        with pytest.raises(ValueError, match="Email is required"):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_raises_on_empty_email(self):
        """Test that missing email key raises ValueError."""
        rows = [
            {"first_name": "John", "last_name": "Doe"},
        ]

        with pytest.raises(ValueError, match="Email is required"):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_with_invalid_uuid(self):
        """Test that invalid UUID raises ValueError."""
        rows = [
            {"email": "test@example.com", "id": "not-a-valid-uuid"},
        ]

        with pytest.raises(ValueError):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_with_empty_id(self):
        """Test that empty id becomes None."""
        rows = [
            {"email": "test@example.com", "id": ""},
        ]

        series = CreateGuestFactory.create_commands(rows)

        assert series.commands[0].user_id is None

    def test_create_commands_with_valid_uuid(self):
        """Test that valid UUID is parsed correctly."""
        user_id = uuid4()
        rows = [
            {"email": "test@example.com", "id": str(user_id)},
        ]

        series = CreateGuestFactory.create_commands(rows)

        assert series.commands[0].user_id == user_id

    def test_create_commands_with_missing_optional_fields(self):
        """Test that missing optional fields get defaults."""
        rows = [
            {"email": "test@example.com"},
        ]

        series = CreateGuestFactory.create_commands(rows)

        cmd = series.commands[0]
        assert cmd.email == "test@example.com"
        assert cmd.first_name == ""
        assert cmd.last_name == ""
        assert cmd.lang == "en"
        assert cmd.user_id is None
        assert cmd.send_email is False

    def test_create_commands_with_all_fields(self):
        """Test that all fields are correctly mapped."""
        user_id = uuid4()
        rows = [
            {
                "id": str(user_id),
                "email": "test@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "lang": "nl",
            },
        ]

        series = CreateGuestFactory.create_commands(rows)

        cmd = series.commands[0]
        assert cmd.user_id == user_id
        assert cmd.email == "test@example.com"
        assert cmd.first_name == "John"
        assert cmd.last_name == "Doe"
        assert cmd.lang == "nl"

    def test_create_commands_whitespace_handling(self):
        """Test that whitespace is stripped from fields."""
        rows = [
            {"email": "  test@example.com  ", "first_name": "  John  ", "last_name": "  Doe  "},
        ]

        series = CreateGuestFactory.create_commands(rows)

        cmd = series.commands[0]
        assert cmd.email == "test@example.com"
        assert cmd.first_name == "John"
        assert cmd.last_name == "Doe"

    def test_create_commands_default_lang(self):
        """Test that missing lang defaults to 'en'."""
        rows = [
            {"email": "test@example.com", "lang": ""},
        ]

        series = CreateGuestFactory.create_commands(rows)

        assert series.commands[0].lang == "en"

    def test_create_commands_multiple_rows(self):
        """Test creating multiple commands."""
        rows = [
            {"email": "a@test.com"},
            {"email": "b@test.com"},
            {"email": "c@test.com"},
        ]

        series = CreateGuestFactory.create_commands(rows)

        assert len(series.commands) == 3
        assert series.commands[0].email == "a@test.com"
        assert series.commands[1].email == "b@test.com"
        assert series.commands[2].email == "c@test.com"

    def test_create_commands_with_invalid_email_no_at(self):
        """Test that email without @ raises ValueError."""
        rows = [
            {"email": "invalid-email.com", "first_name": "John"},
        ]

        with pytest.raises(ValueError, match="Invalid email address"):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_with_invalid_email_no_domain(self):
        """Test that email without domain raises ValueError."""
        rows = [
            {"email": "test@", "first_name": "John"},
        ]

        with pytest.raises(ValueError, match="Invalid email address"):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_with_invalid_email_no_local_part(self):
        """Test that email without local part raises ValueError."""
        rows = [
            {"email": "@example.com", "first_name": "John"},
        ]

        with pytest.raises(ValueError, match="Invalid email address"):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_with_invalid_email_no_tld(self):
        """Test that email without TLD raises ValueError."""
        rows = [
            {"email": "test@example", "first_name": "John"},
        ]

        with pytest.raises(ValueError, match="Invalid email address"):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_with_invalid_email_spaces(self):
        """Test that email with spaces raises ValueError."""
        rows = [
            {"email": "test @example.com", "first_name": "John"},
        ]

        with pytest.raises(ValueError, match="Invalid email address"):
            CreateGuestFactory.create_commands(rows)

    def test_create_commands_with_valid_email_complex(self):
        """Test that valid complex email addresses are accepted."""
        rows = [
            {"email": "user.name+tag@example.co.uk"},
            {"email": "test123@sub.domain.example.com"},
        ]

        series = CreateGuestFactory.create_commands(rows)

        assert len(series.commands) == 2
        assert series.commands[0].email == "user.name+tag@example.co.uk"
        assert series.commands[1].email == "test123@sub.domain.example.com"
