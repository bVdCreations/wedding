import json
import logging
from typing import Any, Protocol

from fastapi import APIRouter, Depends, HTTPException, Request

from src.config.settings import settings
from src.webhooks import urls

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
        from svix.webhooks import Webhook, WebhookVerificationError

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
            from_=settings.emails_from,
            passthrough=False,
            text="See attached forwarded message.",
            html="<p>See attached forwarded message.</p>",
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


@router.post(urls.RESEND_WEBHOOK_RECEIVING_URL)
async def resend_receiving_webhook(
    request: Request,
    verifier: WebhookVerifier = Depends(get_webhook_verifier),
    forwarder: EmailForwarder = Depends(get_email_forwarder),
) -> dict[str, str]:
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
        "svix-id": request.headers.get("svix-id"),
        "svix-timestamp": request.headers.get("svix-timestamp"),
        "svix-signature": request.headers.get("svix-signature"),
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
