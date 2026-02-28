"""Unit tests for ReceivedEmail schema validation."""

from datetime import timezone

import pytest

from src.webhooks.schema import ReceivedEmail

BASE_EMAIL = {
    "object": "email",
    "id": "abc-123",
    "to": ["to@example.com"],
    "from": "Sender <sender@example.com>",
    "subject": "Hello",
    "message_id": "<msg@example.com>",
    "raw": {
        "download_url": "https://example.com/raw",
        "expires_at": "2026-02-28T22:00:00+00:00",
    },
}


def make_email(created_at: str) -> ReceivedEmail:
    return ReceivedEmail.model_validate({**BASE_EMAIL, "created_at": created_at})


def test_created_at_accepts_standard_iso_offset():
    email = make_email("2026-02-28 21:28:27.482506+00:00")
    assert email.created_at.tzinfo is not None
    assert email.created_at.utcoffset().total_seconds() == 0


def test_created_at_accepts_short_utc_offset():
    """Resend sends +00 instead of +00:00 — should be normalised without error."""
    email = make_email("2026-02-28 21:28:27.482506+00")
    assert email.created_at.tzinfo is not None
    assert email.created_at.utcoffset().total_seconds() == 0


def test_created_at_short_and_standard_parse_to_same_value():
    short = make_email("2026-02-28 21:28:27.482506+00")
    standard = make_email("2026-02-28 21:28:27.482506+00:00")
    assert short.created_at == standard.created_at


def test_created_at_rejects_invalid_string():
    with pytest.raises(Exception):
        make_email("not-a-date")
