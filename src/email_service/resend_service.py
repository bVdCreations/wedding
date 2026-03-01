from typing import Protocol
from uuid import UUID

import httpx

from src.email_service.base import EmailServiceBase
from src.email_service.email_logger import EmailLogger, NoOpEmailLogger
from src.email_service.templates import EmailTemplates
from src.guests.dtos import Language


class ResendEmailConfig(Protocol):
    resend_api_key: str
    emails_from: str


class ResendEmailService(EmailServiceBase):
    def __init__(
        self, 
        config: ResendEmailConfig,
        email_logger: EmailLogger | None = None,
    ):
        self._config = config
        self.email_logger = email_logger or NoOpEmailLogger()

    async def _send(
        self,
        to_address: str,
        subject: str,
        html_body: str,
        text_body: str,
        email_type: str,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
        language: Language | None = None,
    ) -> str:
        """Send email via Resend and log via injected logger."""
        
        # Log attempt before sending
        log_uuid = await self.email_logger.log_email_attempt(
            to_address=to_address,
            from_address=self._config.emails_from,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type=email_type,
            guest_id=guest_id,
            user_id=user_id,
            language=language,
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self._config.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self._config.emails_from,
                        "to": [to_address],
                        "subject": subject,
                        "html": html_body,
                        "text": text_body,
                    },
                )
                response.raise_for_status()
                
                # Extract Resend email ID from response
                response_data = response.json()
                resend_email_id = response_data.get("id")
                
                # Log success
                await self.email_logger.log_email_success(
                    log_uuid=log_uuid,
                    resend_email_id=resend_email_id,
                )
                
                return resend_email_id
                
        except httpx.HTTPStatusError as e:
            # Log failure
            await self.email_logger.log_email_failure(
                log_uuid=log_uuid,
                error_message=str(e),
            )
            raise

    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        event_date: str,
        event_location: str,
        rsvp_url: str,
        response_deadline: str,
        language: Language = Language.EN,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        subject, html_template, text_template = EmailTemplates.get_invitation_templates(language)

        html_body = html_template.format(
            guest_name=guest_name,
            event_date=event_date,
            event_location=event_location,
            rsvp_url=rsvp_url,
            response_deadline=response_deadline,
            couple_names="Bastiaan & Gemma",
        )
        text_body = text_template.format(
            guest_name=guest_name,
            event_date=event_date,
            event_location=event_location,
            rsvp_url=rsvp_url,
            response_deadline=response_deadline,
            couple_names="Bastiaan & Gemma",
        )

        await self._send(
            to_address=to_address,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type="invitation",
            guest_id=guest_id,
            user_id=user_id,
            language=language,
        )

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
        language: Language = Language.EN,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        subject, html_template, text_template = EmailTemplates.get_confirmation_templates(language)

        html_body = html_template.format(
            guest_name=guest_name,
            attending=attending,
            dietary=dietary,
            couple_names="Bastiaan & Gemma",
        )
        text_body = text_template.format(
            guest_name=guest_name,
            attending=attending,
            dietary=dietary,
            couple_names="Bastiaan & Gemma",
        )

        await self._send(
            to_address=to_address,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type="confirmation",
            guest_id=guest_id,
            user_id=user_id,
            language=language,
        )

    async def send_invite_one_plus_one(
        self,
        to_address: str,
        guest_name: str,
        plus_one_details: dict,
        language: Language = Language.EN,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        pass

