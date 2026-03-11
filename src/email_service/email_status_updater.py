from abc import ABC, abstractmethod
from datetime import UTC, datetime

from sqlalchemy import select

from src.config.database import async_session_manager
from src.config.logging import get_logger
from src.guests.repository.orm_models import EmailLog

logger = get_logger(__name__)


class EmailStatusUpdater(ABC):
    """Abstract base class for updating email delivery status."""

    @abstractmethod
    async def update_status(
        self,
        resend_email_id: str,
        event_type: str,
        event_data: dict,
    ) -> bool:
        """
        Update email log status based on webhook event.

        Args:
            resend_email_id: Resend's email ID
            event_type: Event type (email.sent, email.delivered, etc.)
            event_data: Full event data payload

        Returns:
            True if update successful, False if email log not found
        """
        pass


class SQLEmailStatusUpdater(EmailStatusUpdater):
    """SQL database implementation of EmailStatusUpdater."""

    async def update_status(
        self,
        resend_email_id: str,
        event_type: str,
        event_data: dict,
    ) -> bool:
        logger.info(f"Updating email status for {resend_email_id} to {event_type}")

        event_to_status = {
            "email.sent": "sent",
            "email.delivered": "delivered",
            "email.bounced": "bounced",
            "email.delivery_delayed": "sent",  # Keep as sent, just note the delay
            "email.complained": "complained",
        }

        new_status = event_to_status.get(event_type)
        if not new_status:
            logger.warning(f"Unknown event type: {event_type}")
            return False

        async with async_session_manager() as session:
            result = await session.execute(
                select(EmailLog).where(EmailLog.resend_email_id == resend_email_id)
            )
            email_log = result.scalar_one_or_none()

            if not email_log:
                logger.warning(f"No EmailLog found for resend_email_id={resend_email_id}")
                return False

            email_log.status = new_status
            email_log.last_webhook_event = event_type
            email_log.last_webhook_at = datetime.now(UTC)

            if event_type == "email.bounced":
                bounce_type = event_data.get("bounce_type")
                bounce_reason = event_data.get("reason")
                email_log.error_message = f"Bounced: {bounce_type} - {bounce_reason}"
                logger.warning(
                    f"Email bounced for {resend_email_id}: {bounce_type} - {bounce_reason}"
                )

            await session.commit()
            logger.info(f"Successfully updated email status for {resend_email_id} to {new_status}")
            return True


class NoOpEmailStatusUpdater(EmailStatusUpdater):
    """No-op implementation for testing."""

    async def update_status(
        self,
        resend_email_id: str,
        event_type: str,
        event_data: dict,
    ) -> bool:
        return True
