from src.config.settings import settings
from src.email_service.base import EmailServiceBase
from src.email_service.resend_service import ResendEmailService
from src.email_service.smtp_service import SMTPEmailService
from src.email_service.templates import EmailTemplates


def get_email_service() -> EmailServiceBase:
    if settings.resend_api_key:
        return ResendEmailService()
    return SMTPEmailService()


__all__ = [
    "EmailServiceBase",
    "EmailTemplates",
    "get_email_service",
]
