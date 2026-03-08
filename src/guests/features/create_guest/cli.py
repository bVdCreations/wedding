"""CLI helpers for guest import."""

import csv
from pathlib import Path
from typing import Protocol

from src.guests.features.create_guest.command import (
    CommandStatus,
    CreateGuestFactory,
    CreateGuestSeriesCommand,
    CreateGuestSeriesResult,
)
from src.guests.features.create_guest.handler import CreateGuestHandler


class TyperProtocol(Protocol):
    """Protocol for typer instance - enables testing with mocks."""

    class Colors:
        RED: str
        GREEN: str
        YELLOW: str
        BLUE: str

    colors: Colors

    def echo(self, msg: str = "") -> None: ...
    def secho(self, msg: str, fg: str | None = None) -> None: ...
    def pause(self) -> None: ...

    class Exit(SystemExit):
        def __init__(self, code: int = 0) -> None: ...


class ImportGuests:
    """Import guests from CSV file - handler + typer injected for testability."""

    def __init__(
        self,
        handler: CreateGuestHandler,
        typer_instance: "TyperProtocol",
        overwrite_ask_confirmation: bool = False,
    ):
        self._handler = handler
        self._typer = typer_instance
        self._overwrite_ask_confirmation = overwrite_ask_confirmation

    async def __call__(
        self,
        csv_file: Path,
        dry_run: bool = False,
        send_emails: bool = False,
    ) -> CreateGuestSeriesResult:
        """Import guests from a CSV file."""

        try:
            series = CreateGuestFactory.create_commands(
                self._read_csv(csv_file),
                send_email=send_emails,
            )
        except FileNotFoundError:
            self._typer.secho(f"File not found: {csv_file}", fg=self._typer.colors.RED)
            raise self._typer.Exit(1)
        except ValueError as e:
            self._typer.secho(str(e), fg=self._typer.colors.RED)
            raise self._typer.Exit(1)

        if dry_run:
            self._typer.secho(
                f"Would create {len(series.commands)} guests:", fg=self._typer.colors.YELLOW
            )
            self._write_input(series)
            raise self._typer.Exit(0)

        else:
            self._typer.secho(
                f"Creating {len(series.commands)} guests:", fg=self._typer.colors.YELLOW
            )
            self._write_input(series)
            self._ask_confirmation()
            result = await self._handler.execute(series)

            self._output_result(result, send_emails)

            return result

    def _write_input(self, series: CreateGuestSeriesCommand) -> None:
        """Write input to CSV file."""
        for cmd in series.commands:
            self._typer.echo(f"  - {cmd.email}: {cmd.first_name} {cmd.last_name} ({cmd.lang})")

    def _ask_confirmation(self) -> None:
        """Ask for confirmation before creating guests."""
        if self._overwrite_ask_confirmation:
            return
        else:
            self._typer.echo()
            self._typer.secho(
                "Are you sure you want to create these guests?", fg=self._typer.colors.YELLOW
            )
            self._typer.secho("Press Ctrl+C to cancel.", fg=self._typer.colors.YELLOW)
            self._typer.echo()
            try:
                self._typer.pause()
            except KeyboardInterrupt:
                self._typer.secho("Cancelled.", fg=self._typer.colors.RED)
                raise self._typer.Exit(1)

    def _read_csv(self, csv_file: Path) -> list[dict]:
        """Read and parse CSV file."""
        try:
            with open(csv_file, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except csv.Error as e:
            raise ValueError(f"Error reading CSV: {e}")
        except Exception as e:
            raise ValueError(f"Error reading CSV: {e}")
        if not rows:
            raise ValueError("CSV file is empty")
        return rows

    def _output_result(self, result: CreateGuestSeriesResult, send_emails: bool) -> None:
        """Output import results."""
        t = self._typer

        t.echo()
        t.secho(f"Total: {result.total}", fg=t.colors.BLUE)
        t.secho(f"Created: {result.created}", fg=t.colors.GREEN)
        t.secho(f"Skipped: {result.skipped}", fg=t.colors.YELLOW)
        t.secho(f"Errors: {result.errors}", fg=t.colors.RED)

        if send_emails:
            t.secho(f"Emails sent: {result.emails_sent}", fg=t.colors.GREEN)
            t.secho(f"Emails failed: {result.emails_failed}", fg=t.colors.RED)

        t.echo()
        t.secho("Results:", fg=t.colors.BLUE)
        for r in result.results:
            if r.status == CommandStatus.CREATED:
                fg = t.colors.GREEN
                status_label = "CREATED"
            elif r.status == CommandStatus.SKIPPED:
                fg = t.colors.YELLOW
                status_label = "SKIPPED"
            else:
                fg = t.colors.RED
                status_label = "ERROR"

            t.secho(f"  [{status_label}] {r.email}: {r.message}", fg=fg)
