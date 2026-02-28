import httpx

from src.config.settings import settings
from src.email_service.base import EmailServiceBase
from src.email_service.templates import EmailTemplates
from src.guests.dtos import Language


class ResendEmailService(EmailServiceBase):
    def __init__(self):
        self.from_address = settings.emails_from

    async def _send(
        self,
        to_address: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.from_address,
                    "to": [to_address],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body,
                },
            )
            response.raise_for_status()

    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        event_date: str,
        event_location: str,
        rsvp_url: str,
        response_deadline: str,
        language: Language = Language.EN,
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

        await self._send(to_address, subject, html_body, text_body)

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
        language: Language = Language.EN,
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

        await self._send(to_address, subject, html_body, text_body)

    async def send_invite_one_plus_one(
        self,
        to_address: str,
        guest_name: str,
        plus_one_details: dict,
        language: Language = Language.EN,
    ) -> None:
        pass
