import pytest

from src.webhooks import urls
from src.webhooks.router import get_email_forwarder, get_webhook_verifier


class MockVerifier:
    """Mock webhook verifier that always succeeds."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.calls = []

    def __call__(self, payload: str, headers: dict) -> dict:
        self.calls.append({"payload": payload, "headers": headers})
        if self.should_fail:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Mock signature failed")
        return {"type": "email.received", "data": {"email_id": "test-123"}}


class MockForwarder:
    """Mock email forwarder that records calls."""

    def __init__(self):
        self.calls = []
        self.should_fail = False

    async def __call__(self, email_id: str) -> dict:
        self.calls.append({"email_id": email_id})
        if self.should_fail:
            raise RuntimeError("Forward failed")
        return {"id": f"forwarded-{email_id}"}


@pytest.mark.asyncio
async def test_forward_success(client_factory):
    """Test successful email forwarding."""
    mock_verifier = MockVerifier()
    mock_forwarder = MockForwarder()

    overrides = {
        get_webhook_verifier: lambda: mock_verifier,
        get_email_forwarder: lambda: mock_forwarder,
    }

    async with client_factory(overrides) as client:
        response = await client.post(
            urls.RESEND_WEBHOOK_RECEIVING_URL,
            json={"type": "email.received", "data": {"email_id": "test-123"}},
            headers={
                "svix-id": "msg_123",
                "svix-timestamp": "1234567890",
                "svix-signature": "valid-signature",
            },
        )

    assert response.status_code == 200
    assert len(mock_verifier.calls) == 1
    assert len(mock_forwarder.calls) == 1
    assert mock_forwarder.calls[0]["email_id"] == "test-123"


@pytest.mark.asyncio
async def test_signature_verification_failure(client_factory):
    """Test webhook rejects invalid signatures."""
    mock_verifier = MockVerifier(should_fail=True)

    overrides = {
        get_webhook_verifier: lambda: mock_verifier,
    }

    async with client_factory(overrides) as client:
        response = await client.post(
            urls.RESEND_WEBHOOK_RECEIVING_URL,
            json={"type": "email.received", "data": {"email_id": "test-123"}},
            headers={
                "svix-id": "msg_123",
                "svix-timestamp": "1234567890",
                "svix-signature": "invalid",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forwarding_failure(client_factory):
    """Test webhook returns 500 when forwarding fails."""
    mock_verifier = MockVerifier()
    mock_forwarder = MockForwarder()
    mock_forwarder.should_fail = True

    overrides = {
        get_webhook_verifier: lambda: mock_verifier,
        get_email_forwarder: lambda: mock_forwarder,
    }

    async with client_factory(overrides) as client:
        response = await client.post(
            urls.RESEND_WEBHOOK_RECEIVING_URL,
            json={"type": "email.received", "data": {"email_id": "test-123"}},
            headers={
                "svix-id": "msg_123",
                "svix-timestamp": "1234567890",
                "svix-signature": "valid",
            },
        )

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_non_email_received_ignored(client_factory):
    """Test non-email.received events are ignored."""
    mock_verifier = MockVerifier()
    mock_forwarder = MockForwarder()

    overrides = {
        get_webhook_verifier: lambda: mock_verifier,
        get_email_forwarder: lambda: mock_forwarder,
    }

    async with client_factory(overrides) as client:
        response = await client.post(
            urls.RESEND_WEBHOOK_RECEIVING_URL,
            json={"type": "email.sent", "data": {"email_id": "test-123"}},
            headers={
                "svix-id": "msg_123",
                "svix-timestamp": "1234567890",
                "svix-signature": "valid",
            },
        )

    assert response.status_code == 200
    assert len(mock_forwarder.calls) == 0  # Not forwarded


@pytest.mark.asyncio
async def test_missing_email_id(client_factory):
    """Test webhook handles missing email_id gracefully."""
    mock_verifier = MockVerifier()
    mock_forwarder = MockForwarder()

    overrides = {
        get_webhook_verifier: lambda: mock_verifier,
        get_email_forwarder: lambda: mock_forwarder,
    }

    async with client_factory(overrides) as client:
        response = await client.post(
            urls.RESEND_WEBHOOK_RECEIVING_URL,
            json={"type": "email.received", "data": {}},
            headers={
                "svix-id": "msg_123",
                "svix-timestamp": "1234567890",
                "svix-signature": "valid",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
    assert len(mock_forwarder.calls) == 0  # Not forwarded
