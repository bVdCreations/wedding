"""Tests for ImportGuests class."""

import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

import pytest

from src.guests.features.create_guest.command import (
    CommandStatus,
    CreateGuestCommandResult,
    CreateGuestSeriesResult,
)
from src.guests.features.create_guest.handler import CreateGuestHandler
from src.guests.features.create_guest.cli import ImportGuests


class MockTyper:
    """Mock typer for testing output."""

    def __init__(self):
        self.colors = type(
            "Colors",
            (),
            {
                "BLUE": "blue",
                "GREEN": "green",
                "YELLOW": "yellow",
                "RED": "red",
            },
        )()
        self.output = []
        self.exit_code = None
        self.paused = False

    def echo(self, msg=""):
        self.output.append(msg)

    def secho(self, msg, fg=None):
        self.output.append(f"[{fg}] {msg}")

    def pause(self):
        self.paused = True

    def Exit(self, code=0):
        self.exit_code = code
        raise SystemExit(code)


@pytest.fixture
def csv_file():
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("guest_id,email,first_name,last_name,lang\n")
        csv_path = Path(f.name)
    yield csv_path
    csv_path.unlink(missing_ok=True)


class TestImportGuestsValidation:
    """Test validation in ImportGuests."""

    @pytest.mark.asyncio
    async def test_file_not_found(self, csv_file):
        """Test SystemExit for non-existent file."""
        csv_file.unlink()

        mock_handler = MagicMock(spec=CreateGuestHandler)
        mock_typer = MockTyper()
        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)

        with pytest.raises(SystemExit):
            await import_guests(csv_file, send_emails=False)

    @pytest.mark.asyncio
    async def test_empty_csv(self, csv_file):
        """Test SystemExit for empty CSV."""
        csv_file.write_text("")

        mock_handler = MagicMock(spec=CreateGuestHandler)
        mock_typer = MockTyper()
        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)

        with pytest.raises(SystemExit):
            await import_guests(csv_file, send_emails=False)

    @pytest.mark.asyncio
    async def test_invalid_email(self, csv_file):
        """Test SystemExit for invalid email."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,invalid-email,John,Doe,en\n"
        )

        mock_handler = AsyncMock(spec=CreateGuestHandler)
        mock_typer = MockTyper()
        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)

        with pytest.raises(SystemExit):
            await import_guests(csv_file, send_emails=False)

    @pytest.mark.asyncio
    async def test_missing_email(self, csv_file):
        """Test SystemExit for missing email."""
        csv_file.write_text("guest_id,email,first_name,last_name,lang\n,,John,Doe,en\n")

        mock_handler = MagicMock(spec=CreateGuestHandler)
        mock_typer = MockTyper()
        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)

        with pytest.raises(SystemExit):
            await import_guests(csv_file, send_emails=False)


class TestImportGuestsSuccess:
    """Test successful import scenarios."""

    @pytest.mark.asyncio
    async def test_import_single_guest(self, csv_file):
        """Test importing a single new guest."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        guest_id = uuid4()
        mock_result = CreateGuestSeriesResult(
            total=1,
            created=1,
            skipped=0,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="john@example.com",
                    message="User and guest created",
                    guest_id=guest_id,
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        result = await import_guests(csv_file, send_emails=False)

        assert result.created == 1
        assert result.errors == 0
        assert result.results[0].email == "john@example.com"
        mock_handler.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_multiple_guests(self, csv_file):
        """Test importing multiple guests."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n"
            ",a@test.com,A,Aa,en\n"
            ",b@test.com,B,Bb,en\n"
            ",c@test.com,C,Cc,en\n"
        )

        mock_result = CreateGuestSeriesResult(
            total=3,
            created=3,
            skipped=0,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email=f"{l}@test.com",
                    message="OK",
                    guest_id=uuid4(),
                )
                for l in ["a", "b", "c"]
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        result = await import_guests(csv_file, send_emails=False)

        assert result.created == 3


class TestImportGuestsDuplicates:
    """Test duplicate handling."""

    @pytest.mark.asyncio
    async def test_import_with_duplicates(self, csv_file):
        """Test that duplicate emails are skipped."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n"
            ",new@example.com,New,User,en\n"
            ",existing@example.com,Existing,User,en\n"
        )

        mock_result = CreateGuestSeriesResult(
            total=2,
            created=1,
            skipped=1,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="new@example.com",
                    message="User and guest created",
                    guest_id=uuid4(),
                ),
                CreateGuestCommandResult(
                    status=CommandStatus.SKIPPED,
                    email="existing@example.com",
                    message="Guest already exists for this email",
                ),
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        result = await import_guests(csv_file, send_emails=False)

        assert result.created == 1
        assert result.skipped == 1


class TestImportGuestsSendEmails:
    """Test email sending flag."""

    @pytest.mark.asyncio
    async def test_send_emails_flag_passed(self, csv_file):
        """Test that send_emails flag is set on commands."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        mock_result = CreateGuestSeriesResult(
            total=1,
            created=1,
            skipped=0,
            errors=0,
            emails_sent=1,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="john@example.com",
                    message="User and guest created",
                    guest_id=uuid4(),
                    email_status="sent",
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        result = await import_guests(csv_file, send_emails=True)

        assert result.emails_sent == 1


class TestImportGuestsSkipGuestId:
    """Test that rows with guest_id are skipped."""

    @pytest.mark.asyncio
    async def test_skips_rows_with_guest_id(self, csv_file):
        """Rows with guest_id should be skipped by factory."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n"
            "abc-123,existing@example.com,Existing,User,en\n"
            ",new@example.com,New,User,en\n"
        )

        mock_result = CreateGuestSeriesResult(
            total=1,
            created=1,
            skipped=0,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="new@example.com",
                    message="User and guest created",
                    guest_id=uuid4(),
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        result = await import_guests(csv_file, send_emails=False)

        assert result.total == 1


class TestImportGuestsDryRun:
    """Test dry-run functionality."""

    @pytest.mark.asyncio
    async def test_dry_run_outputs_preview(self, csv_file):
        """Test that dry_run shows preview without creating."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        mock_handler = AsyncMock()
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)

        with pytest.raises(SystemExit) as exc_info:
            await import_guests(csv_file, dry_run=True, send_emails=False)

        assert exc_info.value.code == 0
        assert any("Would create 1 guests" in line for line in mock_typer.output)
        mock_handler.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run_shows_guests_list(self, csv_file):
        """Test that dry_run shows the list of guests."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,a@test.com,Aa,Aa,en\n,b@test.com,Bb,Bb,en\n"
        )

        mock_handler = AsyncMock()
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)

        with pytest.raises(SystemExit):
            await import_guests(csv_file, dry_run=True, send_emails=False)

        assert any("a@test.com" in line for line in mock_typer.output)
        assert any("b@test.com" in line for line in mock_typer.output)


class TestImportGuestsConfirmation:
    """Test confirmation prompt."""

    @pytest.mark.asyncio
    async def test_asks_confirmation(self, csv_file):
        """Test that confirmation is asked before creating."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        mock_result = CreateGuestSeriesResult(
            total=1,
            created=1,
            skipped=0,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="john@example.com",
                    message="User and guest created",
                    guest_id=uuid4(),
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer)

        await import_guests(csv_file, send_emails=False)

        assert mock_typer.paused
        assert any("Are you sure" in line for line in mock_typer.output)

    @pytest.mark.asyncio
    async def test_skip_confirmation_with_flag(self, csv_file):
        """Test that confirmation is skipped with overwrite_ask_confirmation."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        mock_result = CreateGuestSeriesResult(
            total=1,
            created=1,
            skipped=0,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="john@example.com",
                    message="User and guest created",
                    guest_id=uuid4(),
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_typer = MockTyper()

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)

        await import_guests(csv_file, send_emails=False)

        assert not mock_typer.paused


class TestImportGuestsOutput:
    """Test output formatting."""

    @pytest.mark.asyncio
    async def test_outputs_results(self, csv_file):
        """Test that results are output correctly."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        mock_typer = MockTyper()
        mock_result = CreateGuestSeriesResult(
            total=1,
            created=1,
            skipped=0,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="john@example.com",
                    message="User and guest created",
                    guest_id=uuid4(),
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        await import_guests(csv_file, send_emails=False)

        assert any("Created: 1" in line for line in mock_typer.output)
        assert any("Total: 1" in line for line in mock_typer.output)

    @pytest.mark.asyncio
    async def test_outputs_skipped(self, csv_file):
        """Test that skipped results are output correctly."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        mock_typer = MockTyper()
        mock_result = CreateGuestSeriesResult(
            total=1,
            created=0,
            skipped=1,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.SKIPPED,
                    email="john@example.com",
                    message="Guest already exists",
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        await import_guests(csv_file, send_emails=False)

        assert any("Skipped: 1" in line for line in mock_typer.output)

    @pytest.mark.asyncio
    async def test_outputs_creating_message(self, csv_file):
        """Test that 'Creating' message is shown."""
        csv_file.write_text(
            "guest_id,email,first_name,last_name,lang\n,john@example.com,John,Doe,en\n"
        )

        mock_typer = MockTyper()
        mock_result = CreateGuestSeriesResult(
            total=1,
            created=1,
            skipped=0,
            errors=0,
            emails_sent=0,
            emails_failed=0,
            results=[
                CreateGuestCommandResult(
                    status=CommandStatus.CREATED,
                    email="john@example.com",
                    message="User and guest created",
                    guest_id=uuid4(),
                )
            ],
        )

        mock_handler = AsyncMock()
        mock_handler.execute = AsyncMock(return_value=mock_result)

        import_guests = ImportGuests(mock_handler, mock_typer, overwrite_ask_confirmation=True)
        await import_guests(csv_file, send_emails=False)

        assert any("Creating 1 guests" in line for line in mock_typer.output)
