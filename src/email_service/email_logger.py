from abc import ABC, abstractmethod
from uuid import UUID

from src.guests.dtos import Language


class EmailLogger(ABC):
    """Abstract base class for logging email sending operations."""
    
    @abstractmethod
    async def log_email_attempt(
        self,
        to_address: str,
        from_address: str,
        subject: str,
        html_body: str,
        text_body: str,
        email_type: str,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
        language: Language | None = None,
    ) -> UUID:
        """
        Log an email sending attempt before sending.
        
        Returns:
            UUID of the created log entry
        """
        pass
    
    @abstractmethod
    async def log_email_success(
        self,
        log_uuid: UUID,
        resend_email_id: str,
    ) -> None:
        """Update log entry with successful send and Resend email ID."""
        pass
    
    @abstractmethod
    async def log_email_failure(
        self,
        log_uuid: UUID,
        error_message: str,
    ) -> None:
        """Update log entry with failure status and error message."""
        pass


class SQLEmailLogger(EmailLogger):
    """SQL database implementation of EmailLogger."""
    
    async def log_email_attempt(
        self,
        to_address: str,
        from_address: str,
        subject: str,
        html_body: str,
        text_body: str,
        email_type: str,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
        language: Language | None = None,
    ) -> UUID:
        from src.guests.repository.orm_models import EmailLog
        from src.config.database import async_session_manager
        
        email_log = EmailLog(
            to_address=to_address,
            from_address=from_address,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type=email_type,
            guest_id=guest_id,
            user_id=user_id,
            language=language,
            status="pending",
        )
        
        async with async_session_manager() as session:
            session.add(email_log)
            await session.commit()
            await session.refresh(email_log)
            return email_log.uuid
    
    async def log_email_success(
        self,
        log_uuid: UUID,
        resend_email_id: str,
    ) -> None:
        from src.guests.repository.orm_models import EmailLog
        from src.config.database import get_async_session
        
        async with async_session_manager() as session:
            email_log = await session.get(EmailLog, log_uuid)
            if email_log:
                email_log.resend_email_id = resend_email_id
                email_log.status = "sent"
                await session.commit()
    
    async def log_email_failure(
        self,
        log_uuid: UUID,
        error_message: str,
    ) -> None:
        from src.guests.repository.orm_models import EmailLog
        from src.config.database import get_async_session
        
        async with async_session_manager() as session:
            email_log = await session.get(EmailLog, log_uuid)
            if email_log:
                email_log.status = "failed"
                email_log.error_message = error_message
                await session.commit()


class NoOpEmailLogger(EmailLogger):
    """No-op implementation for testing or when logging is disabled."""
    
    async def log_email_attempt(
        self,
        to_address: str,
        from_address: str,
        subject: str,
        html_body: str,
        text_body: str,
        email_type: str,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
        language: Language | None = None,
    ) -> UUID:
        from uuid import uuid4
        return uuid4()
    
    async def log_email_success(
        self,
        log_uuid: UUID,
        resend_email_id: str,
    ) -> None:
        pass
    
    async def log_email_failure(
        self,
        log_uuid: UUID,
        error_message: str,
    ) -> None:
        pass
