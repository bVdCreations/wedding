# Plan: Email Forwarding with Resend Receiving

## Goal

Configure Resend's email receiving feature to forward incoming emails to a destination address using the built-in `forward()` helper method.

## Overview

Resend provides **email receiving** functionality that can receive emails at your custom domain and forward them via webhook. This implementation uses Resend's native `forward()` helper method, which is much simpler than building a custom Cloudflare Worker.

## Architecture

```
[Sender] -> [Resend Email Receiving] -> [Webhook Handler] -> [Resend.forward()] -> [Destination]
```

## Prerequisites

1. **Resend account** with a verified custom domain
2. **Email receiving** enabled on that domain
3. **Resend API key** with `email:read` and `email:write` permissions

## Implementation Steps

### Step 1: Enable Email Receiving

1. Go to **Resend Dashboard** > **Receiving**
2. Add your custom domain (e.g., `yourdomain.com`)
3. Verify DNS records (MX, CNAME)
4. Enable catch-all or create specific routes

### Step 2: Create Webhook Handler (with Dependency Injection)

**File**: `src/webhooks/router.py`

Using FastAPI's dependency injection for testability:

```python
from typing import Any, Callable, Protocol

import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Protocols (interfaces) for dependency injection
# =============================================================================

class WebhookVerifier(Protocol):
    """Protocol for webhook signature verification."""

    def __call__(self, payload: str, headers: dict[str, str]) -> dict[str, Any]:
        """Verify webhook signature and return parsed payload."""
        ...


class EmailForwarder(Protocol):
    """Protocol for email forwarding."""

    async def __call__(self, email_id: str) -> dict:
        """Forward a received email to configured recipients."""
        ...


# =============================================================================
# Default implementations
# =============================================================================

class SvixWebhookVerifier:
    """Default webhook verifier using Svix."""

    def __call__(self, payload: str, headers: dict[str, str]) -> dict[str, Any]:
        from svix import Webhook, WebhookVerificationError

        secret = settings.resend_webhook_secret
        if not secret:
            raise ValueError("Webhook secret not configured")

        wh = Webhook(secret)

        try:
            return wh.verify(payload, headers)
        except WebhookVerificationError as e:
            raise HTTPException(status_code=401, detail=f"Invalid signature: {e}")


class ResendEmailForwarder:
    """Default email forwarder using Resend SDK."""

    async def __call__(self, email_id: str) -> dict:
        from resend import Resend

        resend = Resend(api_key=settings.resend_api_key)

        recipients = settings.get_forward_to_emails()
        if not recipients:
            logger.warning("No forward recipients configured")
            return {"skipped": "no recipients"}

        result = await resend.emails.receiving.forward(
            email_id=email_id,
            to=recipients,
            from_=settings.resend_from_address,
            passthrough=False,
            text=settings.forward_message_text or "See attached forwarded message.",
            html=settings.forward_message_html or "<p>See attached forwarded message.</p>",
        )

        return result


# =============================================================================
# Dependency providers (can be overridden in tests)
# =============================================================================

def get_webhook_verifier() -> WebhookVerifier:
    """Factory for webhook verifier. Override in tests."""
    return SvixWebhookVerifier()


def get_email_forwarder() -> EmailForwarder:
    """Factory for email forwarder. Override in tests."""
    return ResendEmailForwarder()


# =============================================================================
# Webhook endpoint
# =============================================================================

@router.post("/webhooks/resend/receiving")
async def resend_receiving_webhook(
    request: Request,
    verifier: WebhookVerifier = Depends(get_webhook_verifier),
    forwarder: EmailForwarder = Depends(get_email_forwarder),
) -> Dict[str, str]:
    """
    Handle Resend email.received webhook events and forward emails.

    Dependencies are injected for easy testing:
    - verifier: validates webhook signature
    - forwarder: handles email forwarding
    """
    # Get raw body for signature verification
    body = await request.body()
    payload_str = body.decode("utf-8")

    # Extract Svix headers
    headers = {
        "id": request.headers.get("svix-id"),
        "timestamp": request.headers.get("svix-timestamp"),
        "signature": request.headers.get("svix-signature"),
    }

    # Verify signature (injected dependency)
    try:
        verifier(payload_str, headers)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    payload = json.loads(payload_str)
    event_type = payload.get("type")

    if event_type == "email.received":
        email_id = payload.get("data", {}).get("email_id")

        if not email_id:
            logger.warning("Received webhook without email_id")
            return {"status": "ignored"}

        # Forward using injected dependency
        try:
            result = await forwarder(email_id)
            logger.info(f"Forwarded email {email_id}: {result}")
        except Exception as e:
            logger.error(f"Failed to forward email {email_id}: {e}")
            raise HTTPException(status_code=500, detail="Forward failed")
    else:
        # Log all other events for monitoring
        logger.info(f"Received non-email.received event: {event_type} - {payload.get('data', {})}")

    return {"status": "received"}
```

### Step 3: Implement Email Forwarding

**File**: `src/email_service/resend_service.py`

Use Resend's built-in forward helper:

```python
from resend import Resend

async def forward_received_email(email_id: str) -> dict:
    """
    Forward a received email to the configured destinations.

    Uses Resend's built-in forward() helper which automatically
    fetches email content and attachments.
    """
    resend = Resend(api_key=settings.resend_api_key)

    result = await resend.emails.receiving.forward(
        email_id=email_id,
        to=settings.forward_to_emails,  # List of email addresses
        from_=settings.resend_from_address,
    )

    return result
```

**Option A: Single recipient**

```bash
export FORWARD_TO_EMAILS="destination@example.com"
```

**Option B: Multiple recipients**

```bash
export FORWARD_TO_EMAILS="alice@example.com, bob@example.com, charlie@example.com"
```

### Step 4: Configure Settings

**File**: `src/config/settings.py`

```python
from typing import List

# Resend email forwarding
forward_to_emails: List[str] = []  # Comma-separated list of destination emails
resend_from_address: str = "Your Name <hello@yourdomain.com>"
forward_message_text: str = "See attached forwarded message."
forward_message_html: str = "<p>See attached forwarded message.</p>"

def get_forward_to_emails(self) -> List[str]:
    """Parse and validate forward_to_emails from comma-separated string."""
    if not self.forward_to_emails:
        return []
    return [email.strip() for email in self.forward_to_emails.split(",") if email.strip()]
```

Add to `.envrc`:

```bash
# Single recipient
export FORWARD_TO_EMAILS="destination@example.com"

# OR multiple recipients (comma-separated)
export FORWARD_TO_EMAILS="alice@example.com, bob@example.com, charlie@example.com"
export RESEND_FROM_ADDRESS="Your Name <hello@yourdomain.com>"

# Optional: customize forward message
export FORWARD_MESSAGE_TEXT="Fwd: See attached forwarded email."
export FORWARD_MESSAGE_HTML="<p><b>Fwd:</b> See attached forwarded email.</p>"
```

## Forward Options

### Default Forward (Preserves Original)

```python
# Single recipient
await resend.emails.receiving.forward(
    email_id=email_id,
    to="destination@example.com",
    from_="forward@yourdomain.com",
)

# OR multiple recipients
await resend.emails.receiving.forward(
    email_id=email_id,
    to=[
        "alice@example.com",
        "bob@example.com",
        "charlie@example.com",
    ],
    from_="forward@yourdomain.com",
)
```

This preserves the original email content and attachments exactly as received.

### Forward with "Forwarded Message" Style

```python
# Single recipient
await resend.emails.receiving.forward(
    email_id=email_id,
    to="destination@example.com",
    from_="forward@yourdomain.com",
    passthrough=False,
    text="See attached forwarded message.",
    html="<p>See attached forwarded message.</p>",
)

# Multiple recipients
await resend.emails.receiving.forward(
    email_id=email_id,
    to=["alice@example.com", "bob@example.com"],
    from_="forward@yourdomain.com",
    passthrough=False,
    text="See attached forwarded message.",
    html="<p>See attached forwarded message.</p>",
)
```

This adds a "forwarded message" footer with the original email below it.

## Files to Create/Modify

### New Files

- None required (reuses existing webhook infrastructure)

### Modify Existing Files

1. `src/config/settings.py` - Add `forward_to_emails` (list) and `resend_from_address`, add `get_forward_to_emails()` helper
2. `src/webhooks/router.py` - Add receiving webhook endpoint
3. `src/email_service/resend_service.py` - Add `forward_received_email()` method (handles list of recipients)

## Dependencies

No new dependencies needed if using the built-in forward helper. For manual forwarding:

```toml
# Add to pyproject.toml
mailparser = ">=3.0"
```

## Testing

### Unit Testing with Dependency Injection

The webhook uses FastAPI's `Depends()` for injection, making it easy to test without hitting real APIs.

**File**: `src/webhooks/tests/__init__.py` (create if needed)

```python
# Empty - tests directory init
```

**File**: `src/webhooks/tests/test_receiving.py`

```python
import pytest
from src.main import app
from src.webhooks.router import get_webhook_verifier, get_email_forwarder


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
            "/api/v1/webhooks/resend/receiving",
            json={"type": "email.received", "data": {"email_id": "test-123"}},
            headers={"x-webhook-signature": "valid-signature"},
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
            "/api/v1/webhooks/resend/receiving",
            json={"type": "email.received", "data": {"email_id": "test-123"}},
            headers={"x-webhook-signature": "invalid"},
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
            "/api/v1/webhooks/resend/receiving",
            json={"type": "email.received", "data": {"email_id": "test-123"}},
            headers={"x-webhook-signature": "valid"},
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
            "/api/v1/webhooks/resend/receiving",
            json={"type": "email.sent", "data": {"email_id": "test-123"}},
            headers={"x-webhook-signature": "valid"},
        )

    assert response.status_code == 200
    assert len(mock_forwarder.calls) == 0  # Not forwarded
```

**Key testing patterns:**

1. **Use `client_factory`**: From `conftest.py` - provides `async with client_factory(overrides) as client`
2. **Override factories**: Pass overrides dict mapping factory functions to lambda returning mocks
3. **Mock call recording**: Store calls in lists to verify behavior
4. **Error simulation**: Use `should_fail` flags to test error paths
5. **No manual cleanup**: `client_factory` handles cleanup automatically

### Local Testing

Use ngrok to expose your local server:

```bash
ngrok http 8000
```

Configure Resend webhook URL to your ngrok URL.

### Send Test Email

Send an email to `test@yourdomain.com` and verify it gets forwarded to `forward_to_email`.

### Test Webhook Directly

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/resend/receiving \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email.received",
    "data": {
      "email_id": "test_email_id_123"
    }
  }'
```

## Resend Dashboard Configuration

1. Go to **Resend Dashboard** > **Receiving**
2. Add domain: `yourdomain.com`
3. Configure DNS records:
   - MX: `mx.resend.email`
   - CNAME: `resendverify` -> `resend.email`
4. Set catch-all route or create specific routes
5. Add webhook: `https://your-domain.com/api/v1/webhooks/resend/receiving`

## Security Considerations

1. **Verify webhook signatures** - Always verify using Resend's webhook secret
2. **Limit webhook scope** - Only handle `email.received` events
3. **Validate email_id** - Ensure it's a valid UUID before calling forward
4. **Rate limiting** - Resend handles this; implement retry logic for failures

## Monitoring

Log all forwarding events:

```python
# Single recipient
logger.info(f"Forwarded email {email_id} to {forward_to_email}")

# Multiple recipients
logger.info(f"Forwarded email {email_id} to {recipients}")
logger.error(f"Failed to forward email {email_id}: {error}")
```

## Comparison: Built-in vs Manual Forwarding

| Feature              | Built-in `forward()` | Manual Forwarding      |
| -------------------- | -------------------- | ---------------------- |
| Simplicity           | Very simple          | More code              |
| Attachments          | Automatic            | Manual parsing         |
| Inline images        | Automatic            | Manual with content-id |
| Subject modification | No                   | Yes                    |
| Custom headers       | No                   | Yes                    |
| HTML/text extraction | Automatic            | Manual parsing         |

## Cost

- **Resend Receiving**: Free for up to 1,000 emails/month (check current pricing)
- **Resend Sending**: Free tier includes 3,000 emails/month

