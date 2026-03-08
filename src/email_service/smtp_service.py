import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.email_service.base import EmailServiceBase
from src.email_service.template_builder import EmailTemplates
from src.guests.dtos import Language


class SMTPEmailService(EmailServiceBase):
    def __init__(self, session_overwrite: AsyncSession | None = None):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_user
        self.password = settings.smtp_password
        self.from_address = settings.emails_from
        self._session_overwrite = session_overwrite

    def _create_message(
        self,
        to_address: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_address
        msg["To"] = to_address

        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        msg.attach(part1)
        msg.attach(part2)

        return msg

    def _send(self, msg: MIMEMultipart) -> None:
        if self.username and self.password:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self.host, self.port) as server:
                server.send_message(msg)

    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        rsvp_url: str,
        guest_id: UUID,
        language: Language = Language.EN,
        user_id: UUID | None = None,
    ) -> None:
        content = EmailTemplates().get_invitation_templates(language, guest_name, rsvp_url)

        msg = self._create_message(
            to_address=to_address,
            subject=content.subject,
            html_body=content.html_body,
            text_body=content.text_body,
        )

        self._send(msg)

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
        allergies: str = "",
        taking_bus: bool = False,
        language: Language = Language.EN,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        content = EmailTemplates().get_confirmation_templates(
            language, guest_name, attending, dietary, allergies, taking_bus
        )

        msg = self._create_message(
            to_address=to_address,
            subject=content.subject,
            html_body=content.html_body,
            text_body=content.text_body,
        )

        self._send(msg)

    async def send_invite_one_plus_one(
        self,
        to_address: str,
        guest_name: str,
        inviter_name: str,
        rsvp_url: str,
        language: Language = Language.EN,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        content = EmailTemplates().get_plus_one_invitation_templates(
            language, guest_name, inviter_name, rsvp_url
        )

        msg = self._create_message(
            to_address=to_address,
            subject=content.subject,
            html_body=content.html_body,
            text_body=content.text_body,
        )

        self._send(msg)
