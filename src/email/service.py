import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config.settings import settings
from src.email.templates import EmailTemplates


class EmailService:
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_user
        self.password = settings.smtp_password
        self.from_address = settings.emails_from

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

        # Attach both plain text and HTML versions
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
            # For development/testing without authentication
            with smtplib.SMTP(self.host, self.port) as server:
                server.send_message(msg)

    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        event_date: str,
        event_location: str,
        rsvp_url: str,
        response_deadline: str,
        couple_names: str,
    ) -> None:
        html_body = EmailTemplates.INVITATION_HTML.format(
            guest_name=guest_name,
            event_date=event_date,
            event_location=event_location,
            rsvp_url=rsvp_url,
            response_deadline=response_deadline,
            couple_names=couple_names,
        )
        text_body = EmailTemplates.INVITATION_TEXT.format(
            guest_name=guest_name,
            event_date=event_date,
            event_location=event_location,
            rsvp_url=rsvp_url,
            response_deadline=response_deadline,
            couple_names=couple_names,
        )

        msg = self._create_message(
            to_address=to_address,
            subject=EmailTemplates.INVITATION_SUBJECT,
            html_body=html_body,
            text_body=text_body,
        )

        self._send(msg)

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        plus_one: str,
        dietary: str,
        couple_names: str,
    ) -> None:
        html_body = EmailTemplates.CONFIRMATION_HTML.format(
            guest_name=guest_name,
            attending=attending,
            plus_one=plus_one,
            dietary=dietary,
            couple_names=couple_names,
        )
        text_body = EmailTemplates.CONFIRMATION_TEXT.format(
            guest_name=guest_name,
            attending=attending,
            plus_one=plus_one,
            dietary=dietary,
            couple_names=couple_names,
        )

        msg = self._create_message(
            to_address=to_address,
            subject=EmailTemplates.CONFIRMATION_SUBJECT,
            html_body=html_body,
            text_body=text_body,
        )

        self._send(msg)


# Singleton instance
email_service = EmailService()
