from src.config.settings import settings
from src.email.base import EmailServiceBase
from src.email.resend_service import ResendEmailService
from src.email.smtp_service import SMTPEmailService
from src.email.templates import EmailTemplates


def get_email_service() -> EmailServiceBase:
    if settings.resend_api_key:
        return ResendEmailService()
    return SMTPEmailService()


__all__ = [
    "EmailServiceBase",
    "EmailTemplates",
    "get_email_service",
]
