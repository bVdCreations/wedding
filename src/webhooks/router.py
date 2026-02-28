import base64
import json
import logging
from typing import Any, Protocol

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from src.config.settings import settings
from src.webhooks import urls
from src.webhooks.schema import ReceivedEmail

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


class ForwardConfig(Protocol):
    resend_api_key: str
    emails_from: str

    def get_forward_to_emails(self) -> list[str]: ...


class ResendEmailForwarder:
    """Default email forwarder using Resend HTTP API."""

    def __init__(
        self,
        http_client_class: type[httpx.AsyncClient] = httpx.AsyncClient,
        config: ForwardConfig = settings,
    ):
        self._http_client_class = http_client_class
        self._config = config

    async def __call__(self, email_id: str) -> dict:
        recipients = self._config.get_forward_to_emails()
        if not recipients:
            logger.warning("No forward recipients configured")
            return {"skipped": "no recipients"}

        async with self._http_client_class() as client:
            # Step 1: Get email metadata
            email_response = await client.get(
                f"https://api.resend.com/emails/receiving/{email_id}",
                headers={
                    "Authorization": f"Bearer {self._config.resend_api_key}",
                },
            )
            email_response.raise_for_status()
            email_data = ReceivedEmail.model_validate(email_response.json())

            # Step 2: Download raw email content
            raw_download_url = email_data.raw.download_url
            raw_response = await client.get(raw_download_url)
            raw_response.raise_for_status()
            raw_email_content = raw_response.text

            # Step 3: Forward email (passthrough=False style)
            # Attach the raw email as .eml file with custom text/html
            subject = email_data.subject
            if not subject.startswith("Fwd:"):
                subject = f"Fwd: {subject}"

            forward_response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self._config.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self._config.emails_from,
                    "to": recipients,
                    "subject": subject,
                    "text": "See attached forwarded message.",
                    "html": "<p>See attached forwarded message.</p>",
                    "attachments": [
                        {
                            "filename": "forwarded_message.eml",
                            "content": base64.b64encode(raw_email_content.encode("utf-8")).decode(
                                "utf-8"
                            ),
                            "content_type": "message/rfc822",
                        }
                    ],
                },
            )
            forward_response.raise_for_status()
            return forward_response.json()


# =============================================================================
# Dependency providers (can be overridden in tests)
# =============================================================================


def get_webhook_verifier() -> WebhookVerifier:
    """Factory for webhook verifier. Override in tests."""
    return SvixWebhookVerifier()


def get_email_forwarder() -> EmailForwarder:
    """Factory for email forwarder. Override in tests."""
    return ResendEmailForwarder(http_client_class=httpx.AsyncClient, config=settings)


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
    headers: dict[str, str] = {}
    if svix_id := request.headers.get("svix-id"):
        headers["svix-id"] = svix_id
    if svix_timestamp := request.headers.get("svix-timestamp"):
        headers["svix-timestamp"] = svix_timestamp
    if svix_signature := request.headers.get("svix-signature"):
        headers["svix-signature"] = svix_signature

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
