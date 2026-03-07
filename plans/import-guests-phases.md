# Import Guests - Phased Implementation Plan

## Overview

This plan outlines 5 independent phases for implementing the import-guests feature. Each phase can be executed independently and includes both implementation and tests.

---

## Phase 1: Command Classes & Factory

**Goal:** Create the data structures and factory for parsing CSV rows into commands.

### Files to Create

1. `/src/guests/features/create_guest/command.py` - Command classes and factory
2. `/src/guests/features/create_guest/tests/__init__.py`
3. `/src/guests/features/create_guest/tests/test_command.py`

### Implementation

```python
# command.py
from dataclasses import dataclass, field
from uuid import UUID
from enum import Enum

class CommandStatus(Enum):
    CREATED = "created"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class CreateGuestCommandResult:
    status: CommandStatus
    email: str
    message: str
    guest_id: UUID | None = None
    email_status: str | None = None  # "sent", "failed", None (if send_email=False)
    email_error: str | None = None   # Error message if failed

@dataclass
class CreateGuestCommand:
    email: str
    first_name: str = ""
    last_name: str = ""
    lang: str = "en"
    user_id: UUID | None = None
    send_email: bool = False

@dataclass
class CreateGuestSeriesCommand:
    """Wrapper for a series of CreateGuestCommand."""
    commands: list[CreateGuestCommand] = field(default_factory=list)

@dataclass
class CreateGuestSeriesResult:
    """Result DTO for series execution."""
    total: int
    created: int
    skipped: int
    errors: int
    emails_sent: int = 0
    emails_failed: int = 0
    results: list[CreateGuestCommandResult] = field(default_factory=list)

class CreateGuestFactory:
    """Factory to create CreateGuestCommand from CSV rows."""

    @staticmethod
    def create_commands(rows: list[dict]) -> CreateGuestSeriesCommand:
        """Create CreateGuestSeriesCommand from CSV rows."""
        commands = []

        for row in rows:
            email = row.get("email", "").strip()
            if not email:
                raise ValueError("Email is required")

            user_id = row.get("id", "").strip() or None
            if user_id:
                user_id = UUID(user_id)

            command = CreateGuestCommand(
                email=email,
                first_name=row.get("first_name", "").strip() or "",
                last_name=row.get("last_name", "").strip() or "",
                lang=row.get("lang", "").strip() or "en",
                user_id=user_id,
            )
            commands.append(command)

        return CreateGuestSeriesCommand(commands=commands)
```

### Tests (test_command.py)

| Test Name | Description |
|-----------|-------------|
| test_create_commands_with_valid_rows | Valid dicts → correct commands |
| test_create_commands_raises_on_empty_email | Missing email → ValueError |
| test_create_commands_with_invalid_uuid | Invalid UUID → ValueError |
| test_create_commands_with_empty_id | Empty id → user_id is None |
| test_create_commands_with_missing_optional_fields | Only email → defaults applied |
| test_create_commands_with_all_fields | All fields → correctly mapped |

### Success Criteria

- [ ] All command classes defined with correct fields
- [ ] Factory correctly parses CSV rows
- [ ] All tests pass

---

## Phase 2: Handler - Single Command

**Goal:** Create handler that can execute a single CreateGuestCommand.

### Files to Create

1. `/src/guests/features/create_guest/handler.py`

### Files to Modify

- None (uses existing SqlGuestCreateWriteModel)

### Implementation

```python
# handler.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.guests.dtos import GuestAlreadyExistsError, Language
from src.guests.features.create_guest.command import (
    CreateGuestCommand,
    CreateGuestCommandResult,
    CreateGuestSeriesCommand,
    CreateGuestSeriesResult,
    CommandStatus,
)
from src.guests.features.create_guest.write_model import SqlGuestCreateWriteModel


class CreateGuestHandler:
    async def execute(
        self,
        command: CreateGuestCommand | CreateGuestSeriesCommand
    ) -> CreateGuestCommandResult | CreateGuestSeriesResult:
        """Handle both single command and series."""
        
        if isinstance(command, CreateGuestSeriesCommand):
            return await self._execute_series(command)
        
        return await self._execute_single(command)

    async def _execute_single(
        self,
        command: CreateGuestCommand,
        session: AsyncSession | None = None
    ) -> CreateGuestCommandResult:
        """Execute logic for a single command."""
        try:
            # Create write model - send_email=False (handled in Phase 4)
            write_model = SqlGuestCreateWriteModel(
                session_overwrite=session,
            )

            guest_dto = await write_model.create_guest(
                email=command.email,
                first_name=command.first_name or None,
                last_name=command.last_name or None,
                preferred_language=Language(command.lang),
                send_email=False,  # Emails handled separately
            )

            return CreateGuestCommandResult(
                status=CommandStatus.CREATED,
                email=command.email,
                message="Guest created",
                guest_id=guest_dto.id,
            )

        except GuestAlreadyExistsError as e:
            return CreateGuestCommandResult(
                status=CommandStatus.ERROR,
                email=command.email,
                message=str(e),
            )
        except Exception as e:
            return CreateGuestCommandResult(
                status=CommandStatus.ERROR,
                email=command.email,
                message=str(e),
            )
```

### Tests (test_handler_single.py)

| Test Name | Setup | Expected |
|-----------|-------|----------|
| test_execute_single_new_user | No existing user | status=CREATED, guest_id!=None |
| test_execute_single_existing_user_no_guest | User exists, no guest | status=CREATED |
| test_execute_single_existing_user_with_guest | User + Guest exists | status=ERROR |
| test_execute_single_user_id_not_found | UUID not in DB | status=ERROR, "User not found" |
| test_execute_single_user_id_guest_exists | User + Guest, using user_id | status=ERROR |
| test_execute_single_user_id_success | User exists, no guest | status=CREATED |

### Success Criteria

- [ ] Single command execution works
- [ ] Handles existing users correctly
- [ ] Handles user_id lookup correctly
- [ ] All tests pass

---

## Phase 3: Handler - Series Command (Phase 1 of 2-Phase)

**Goal:** Add series execution with single transaction - all guests created or none.

### Files to Modify

1. `/src/guests/features/create_guest/handler.py` - Add `_execute_series` method

### Implementation

```python
async def _execute_series(self, command: CreateGuestSeriesCommand) -> CreateGuestSeriesResult:
    """Execute series in a single transaction.
    
    Phase 1: Create all guests
    - Flush after each command
    - Commit only if ALL succeed
    - Rollback ALL if any fails
    """
    async with async_session_manager() as session:
        results = []
        try:
            for cmd in command.commands:
                result = await self._execute_single(cmd, session)
                results.append(result)

                # If any command errored, abort immediately
                if result.status == CommandStatus.ERROR:
                    await session.rollback()
                    return CreateGuestSeriesResult(
                        total=len(command.commands),
                        created=0,
                        skipped=0,
                        errors=len(command.commands),
                        emails_sent=0,
                        emails_failed=0,
                        results=results,
                    )

            # All commands succeeded - commit
            await session.commit()

            return CreateGuestSeriesResult(
                total=len(results),
                created=sum(1 for r in results if r.status == CommandStatus.CREATED),
                skipped=sum(1 for r in results if r.status == CommandStatus.SKIPPED),
                errors=sum(1 for r in results if r.status == CommandStatus.ERROR),
                emails_sent=0,
                emails_failed=0,
                results=results,
            )

        except Exception as e:
            # Any exception - rollback all
            await session.rollback()
            # Mark remaining commands as errors
            for i in range(len(results), len(command.commands)):
                results.append(CreateGuestCommandResult(
                    status=CommandStatus.ERROR,
                    email=command.commands[i].email,
                    message=f"Transaction failed: {str(e)}",
                ))
            return CreateGuestSeriesResult(
                total=len(command.commands),
                created=0,
                skipped=0,
                errors=len(command.commands),
                emails_sent=0,
                emails_failed=0,
                results=results,
            )
```

### Tests (test_handler_series.py)

| Test Name | Input | Expected |
|-----------|-------|----------|
| test_execute_series_all_success | 3 valid commands | created=3, errors=0 |
| test_execute_series_with_one_error | 2nd fails | created=0, errors=3 (rolled back) |
| test_execute_series_empty | Empty series | all zeros |
| test_execute_series_mixed_results | 2 created, 1 skipped | created=2, skipped=1 |

### Success Criteria

- [ ] All commands execute in single transaction
- [ ] Commit only if all succeed
- [ ] Rollback all if any fails
- [ ] All tests pass

---

## Phase 4: Two-Phase Execution (Email Sending)

**Goal:** Add Phase 2 - send emails after successful DB commit.

### Files to Modify

1. `/src/guests/features/create_guest/handler.py` - Add `_send_email` method, update `_execute_series`

### Implementation

```python
async def _execute_series(self, command: CreateGuestSeriesCommand) -> CreateGuestSeriesResult:
    """Execute series in two phases:
    
    Phase 1: Create all guests in a single transaction
    - Flush after each command
    - Commit only if ALL succeed
    - If any fails → rollback ALL
    
    Phase 2: Send emails (only if Phase 1 succeeded)
    - For each command with send_email=True
    - Send invitation email and log to EmailLog
    - Track result in email_status
    """
    # Phase 1: Create all guests
    async with async_session_manager() as session:
        results = []
        try:
            for cmd in command.commands:
                result = await self._execute_single(cmd, session)
                results.append(result)

                if result.status == CommandStatus.ERROR:
                    await session.rollback()
                    return CreateGuestSeriesResult(
                        total=len(command.commands),
                        created=0,
                        skipped=0,
                        errors=len(command.commands),
                        emails_sent=0,
                        emails_failed=0,
                        results=results,
                    )

            # Phase 1 complete - commit all guests
            await session.commit()

        except Exception as e:
            await session.rollback()
            for i in range(len(results), len(command.commands)):
                results.append(CreateGuestCommandResult(
                    status=CommandStatus.ERROR,
                    email=command.commands[i].email,
                    message=f"Transaction failed: {str(e)}",
                ))
            return CreateGuestSeriesResult(
                total=len(command.commands),
                created=0,
                skipped=0,
                errors=len(command.commands),
                emails_sent=0,
                emails_failed=0,
                results=results,
            )

    # Phase 2: Send emails (only if Phase 1 succeeded)
    emails_sent = 0
    emails_failed = 0
    
    for i, result in enumerate(results):
        cmd = command.commands[i]
        
        if not cmd.send_email:
            continue
        
        email_result = await self._send_email(result, cmd)
        
        result.email_status = email_result["status"]
        result.email_error = email_result.get("error")
        
        if email_result["status"] == "sent":
            emails_sent += 1
        else:
            emails_failed += 1

    return CreateGuestSeriesResult(
        total=len(results),
        created=sum(1 for r in results if r.status == CommandStatus.CREATED),
        skipped=sum(1 for r in results if r.status == CommandStatus.SKIPPED),
        errors=sum(1 for r in results if r.status == CommandStatus.ERROR),
        emails_sent=emails_sent,
        emails_failed=emails_failed,
        results=results,
    )

async def _send_email(
    self, 
    result: CreateGuestCommandResult,
    command: CreateGuestCommand
) -> dict:
    """Send invitation email and log to database."""
    try:
        email_service = get_email_service()
        
        await email_service.send_invitation(
            to_address=command.email,
            guest_name=f"{command.first_name} {command.last_name}".strip() or "Guest",
            rsvp_url="...",  # Need to get from guest
            language=Language(command.lang),
            guest_id=result.guest_id,
        )
        
        # Log to EmailLog
        async with async_session_manager() as session:
            email_log = EmailLog(
                to_address=command.email,
                from_address="...",
                subject="...",
                email_type="invitation",
                guest_id=result.guest_id,
                status="sent",
                language=command.lang,
            )
            session.add(email_log)
            await session.commit()
        
        return {"status": "sent"}
        
    except Exception as e:
        # Log failure
        async with async_session_manager() as session:
            email_log = EmailLog(
                to_address=command.email,
                from_address="...",
                subject="...",
                email_type="invitation",
                guest_id=result.guest_id,
                status="failed",
                error_message=str(e),
                language=command.lang,
            )
            session.add(email_log)
            await session.commit()
        
        return {"status": "failed", "error": str(e)}
```

### Tests (test_two_phase.py)

| Test Name | Setup | Expected |
|-----------|-------|----------|
| test_phase1_success_phase2_send_emails | send_email=True | emails_sent = count |
| test_phase1_success_phase2_partial_failure | 1 email fails | emails_sent + emails_failed tracked |
| test_phase1_success_phase2_no_emails | send_email=False | email_status = None |
| test_phase1_failure_rollback | 2nd fails | No Phase 2, all rolled back |
| test_phase2_exception_keeps_phase1 | Phase 2 throws | Guests committed |

### Success Criteria

- [ ] Phase 2 only runs if Phase 1 succeeds
- [ ] Email failures tracked, don't rollback guests
- [ ] Email logs written to database
- [ ] All tests pass

---

## Phase 5: CLI Integration

**Goal:** Add import-guests command to CLI.

### Files to Modify

1. `/cli.py` - Add import-guests command

### Implementation

```python
import csv
import asyncio
from pathlib import Path

import typer

from src.guests.features.create_guest.command import CreateGuestFactory, CreateGuestSeriesCommand
from src.guests.features.create_guest.handler import CreateGuestHandler


@app.command()
def import_guests(
    csv_file: str = typer.Argument(..., help="Path to CSV file"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview without creating"),
    send_emails: bool = typer.Option(False, "--send-emails", "-e", help="Send invitation emails"),
):
    """Import guests from a CSV file.
    
    CSV format: id,email,first_name,last_name,lang
    
    Examples:
        python cli.py import-guests guests.csv
        python cli.py import-guests guests.csv --dry-run
        python cli.py import-guests guests.csv --send-emails
    """
    # Validate file exists
    path = Path(csv_file)
    if not path.exists():
        typer.secho(f"File not found: {csv_file}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    # Read CSV
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        typer.secho("CSV file is empty", fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    
    # Set send_email on all commands based on flag
    # (Need to update factory or handle after)
    
    # Create commands
    series = CreateGuestFactory.create_commands(rows)
    
    # Set send_email on all commands
    for cmd in series.commands:
        cmd.send_email = send_emails
    
    if dry_run:
        # Preview only - don't execute
        typer.secho(f"Would create {len(series.commands)} guests", fg=typer.colors.YELLOW)
        for cmd in series.commands:
            typer.echo(f"  - {cmd.email}: {cmd.first_name} {cmd.last_name}")
        raise typer.Exit(0)
    
    # Execute via handler
    handler = CreateGuestHandler()
    result = asyncio.run(handler.execute(series))
    
    # Output results
    typer.echo(f"\nTotal: {result.total}")
    typer.secho(f"Created: {result.created}", fg=typer.colors.GREEN)
    typer.secho(f"Skipped: {result.skipped}", fg=typer.colors.YELLOW)
    typer.secho(f"Errors: {result.errors}", fg=typer.colors.RED)
    
    if send_emails:
        typer.secho(f"Emails sent: {result.emails_sent}", fg=typer.colors.GREEN)
        typer.secho(f"Emails failed: {result.emails_failed}", fg=typer.colors.RED)
    
    # Per-row feedback
    for r in result.results:
        if r.status == CommandStatus.CREATED:
            fg = typer.colors.GREEN
        elif r.status == CommandStatus.SKIPPED:
            fg = typer.colors.YELLOW
        else:
            fg = typer.colors.RED
        typer.secho(f"  {r.email}: {r.message}", fg=fg)
```

### Tests (test_cli.py)

| Test Name | Input | Expected |
|-----------|-------|----------|
| test_import_guests_file_not_found | Non-existent path | Error + exit 1 |
| test_import_guests_empty_file | Empty CSV | Message + exit 0 |
| test_import_guests_dry_run | Valid CSV + --dry-run | No DB changes |
| test_import_guests_with_send_emails | CSV + --send-emails | Guests + emails |
| test_import_guests_output_format | Valid CSV | Correct output |

### Success Criteria

- [ ] Command accepts csv_file argument
- [ ] --dry-run flag works
- [ ] --send-emails flag works
- [ ] Output shows correct summary
- [ ] All tests pass

---

## Summary

| Phase | Focus | Files | Tests |
|-------|-------|-------|-------|
| 1 | Command classes + Factory | command.py | test_command.py |
| 2 | Single command handler | handler.py | test_handler_single.py |
| 3 | Series + transaction | handler.py | test_handler_series.py |
| 4 | Email sending | handler.py | test_two_phase.py |
| 5 | CLI command | cli.py | test_cli.py |

---

## Execution Order

1. **Phase 1:** Implement command.py + tests → Verify
2. **Phase 2:** Implement handler single + tests → Verify
3. **Phase 3:** Implement handler series + tests → Verify
4. **Phase 4:** Add email phase + tests → Verify
5. **Phase 5:** Add CLI + tests → Verify

Each phase builds on the previous and can be tested independently.