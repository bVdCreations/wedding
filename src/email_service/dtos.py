from dataclasses import dataclass
from enum import Enum


class EmailStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"


@dataclass
class EmailResult:
    status: EmailStatus
    error: str | None = None
