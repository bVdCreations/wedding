from src.config.settings import settings
from src.email_service.base import EmailServiceBase
from src.email_service.email_logger import SQLEmailLogger
from src.email_service.resend_service import ResendEmailService
from src.email_service.smtp_service import SMTPEmailService
from src.email_service.templates import EmailTemplates


def get_email_service() -> EmailServiceBase:
    if settings.resend_api_key:
        email_logger = SQLEmailLogger()
        return ResendEmailService(config=settings, email_logger=email_logger)
    return SMTPEmailService()


__all__ = [
    "EmailServiceBase",
    "EmailTemplates",
    "get_email_service",
]
