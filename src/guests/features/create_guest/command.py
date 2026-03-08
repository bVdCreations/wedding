from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from src.email_service.dtos import EmailResult

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


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
    email_error: str | None = None  # Error message if failed

    def update_email_result(self, email_result: EmailResult) -> None:
        self.email_status = email_result.status.value
        self.email_error = email_result.error


@dataclass
class CreateGuestCommand:
    email: str
    first_name: str = ""
    last_name: str = ""
    lang: str = "en"
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
            if row.get("guest_id", "").strip():
                continue
            email = row.get("email", "").strip()
            if not email:
                raise ValueError("Email is required")
            if not EMAIL_REGEX.match(email):
                raise ValueError(f"Invalid email address: {email}")

            user_id = row.get("id", "").strip() or None
            if user_id:
                user_id = UUID(user_id)

            command = CreateGuestCommand(
                email=email,
                first_name=row.get("first_name", "").strip() or "",
                last_name=row.get("last_name", "").strip() or "",
                lang=row.get("lang", "").strip() or "en",
            )
            commands.append(command)

        return CreateGuestSeriesCommand(commands=commands)
