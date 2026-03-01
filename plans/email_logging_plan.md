# Email Logging Plan - Resend Integration

## Overview

Add comprehensive logging of all emails sent via Resend API to the database. This enables tracking delivery status, debugging email issues, and maintaining audit history of all wedding communications.

## Goals

1. Log every email sent through Resend with complete parameters and Resend's email ID
2. Track email delivery status via webhooks
3. Provide audit trail for troubleshooting and analytics
4. Maintain referential integrity with existing Guest/User models

## Database Schema

### New Table: `email_logs`

```python
class EmailLog(Base, TimeStamp):
    __tablename__ = "email_logs"
    
    # Core identification
    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    resend_email_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, unique=True)
    
    # Email parameters
    to_address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Email bodies (stored for debugging/audit)
    html_body: Mapped[str] = mapped_column(Text, nullable=True)
    text_body: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Email type and context
    email_type: Mapped[str] = mapped_column(
        Enum("invitation", "confirmation", "reminder", "plus_one_invite", "forwarded", name="email_type_enum"),
        nullable=False,
        index=True
    )
    
    # Foreign keys for context
    guest_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{TableNames.GUESTS.value}.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{TableNames.USERS.value}.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Delivery tracking
    status: Mapped[str] = mapped_column(
        Enum("pending", "sent", "delivered", "bounced", "failed", "complained", name="email_status_enum"),
        default="pending",
        nullable=False,
        index=True,
    )
    
    # Additional metadata
    language: Mapped[str | None] = mapped_column(
        Enum(Language, name="language_enum_ref", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps (inherited from TimeStamp mixin)
    # created_at - when email was initiated
    # updated_at - last status update
    
    # Webhook event tracking
    last_webhook_event: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_webhook_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<EmailLog {self.resend_email_id} to={self.to_address} type={self.email_type} status={self.status}>"
```

### Migration

**Command to create migration**:
```bash
alembic revision -m "add_email_logs_table"
```

**File**: `migrations/versions/YYYY_MM_DD_HHMM-XXXXX_add_email_logs_table.py`

The migration should:
- Create `email_logs` table with all fields from schema above
- Create indexes on: `resend_email_id`, `to_address`, `email_type`, `status`, `guest_id`, `user_id`, `created_at`
- Create enums: `email_type_enum`, `email_status_enum`
- Add foreign keys with `SET NULL` on delete (preserve logs even if guest/user deleted)
- Use timezone-aware DateTime for `last_webhook_at`

**Apply migration**:
```bash
alembic upgrade head
```

## Implementation Steps

### 1. Create Email Logger Abstraction

**File**: `src/email_service/email_logger.py` (new)

Create abstract base class and SQL implementation for email logging:

```python
from abc import ABC, abstractmethod
from datetime import datetime, timezone
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
        from src.config.database import get_async_session
        
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
        
        async with get_async_session() as session:
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
        
        async with get_async_session() as session:
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
        
        async with get_async_session() as session:
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
```

### 2. Create ORM Model

**File**: `src/guests/repository/orm_models.py`

Add `EmailLog` model class with:
- All fields from schema above
- Relationships to `Guest` and `User` (optional, for easy joins)
- `__repr__` for debugging

### 3. Refactor ResendEmailService to Accept Email Logger

**File**: `src/email_service/resend_service.py`

Refactor to accept EmailLogger dependency via constructor. Note that the current implementation uses `ResendEmailConfig` protocol for dependency injection.

```python
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
    ) -> str:  # Return resend_email_id
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
        # Implementation here
        pass
```

**Key changes**:
- Import `Protocol` from `typing` (missing in current implementation)
- Constructor accepts both `config: ResendEmailConfig` (existing) and optional `email_logger: EmailLogger` (new)
- Uses `self._config.resend_api_key` and `self._config.emails_from` instead of settings directly
- `_send()` method uses injected logger instead of direct DB access
- All public methods (`send_invitation`, `send_confirmation`, etc.) accept `guest_id` and `user_id` parameters
- `_send()` signature updated with logging context parameters

### 4. Update Dependency Injection

**File**: `src/config/dependencies.py` (or wherever email service is instantiated)

Update email service factory to inject both config and SQLEmailLogger:

```python
from src.config.settings import settings
from src.email_service.resend_service import ResendEmailService
from src.email_service.email_logger import SQLEmailLogger

def get_email_service() -> ResendEmailService:
    """Factory for email service with SQL logging."""
    email_logger = SQLEmailLogger()
    return ResendEmailService(config=settings, email_logger=email_logger)
```

**Note**: The current implementation uses `ResendEmailConfig` protocol, so `settings` object must implement `resend_api_key` and `emails_from` attributes.

Alternatively, if using direct instantiation in write models, update those locations to pass both config and logger.

### 5. Extend Existing Webhook Handler for Email Status

**File**: `src/email_service/email_status_updater.py` (new)

Create abstraction for updating email status from webhooks:

```python
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID


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
        from src.guests.repository.orm_models import EmailLog
        from src.config.database import get_async_session
        from sqlalchemy import select
        
        # Map Resend event types to our statuses
        event_to_status = {
            "email.sent": "sent",
            "email.delivered": "delivered",
            "email.bounced": "bounced",
            "email.delivery_delayed": "sent",  # Keep as sent, just note the delay
            "email.complained": "complained",
        }
        
        new_status = event_to_status.get(event_type)
        if not new_status:
            return False
        
        # Update EmailLog
        async with get_async_session() as session:
            result = await session.execute(
                select(EmailLog).where(EmailLog.resend_email_id == resend_email_id)
            )
            email_log = result.scalar_one_or_none()
            
            if not email_log:
                return False
            
            email_log.status = new_status
            email_log.last_webhook_event = event_type
            email_log.last_webhook_at = datetime.now(timezone.utc)
            
            # Store error info for bounces
            if event_type == "email.bounced":
                bounce_type = event_data.get("bounce_type")
                bounce_reason = event_data.get("reason")
                email_log.error_message = f"Bounced: {bounce_type} - {bounce_reason}"
            
            await session.commit()
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
```

**File**: `src/webhooks/router.py`

Update to inject `EmailStatusUpdater` dependency:

```python
# Add to imports
from src.email_service.email_status_updater import EmailStatusUpdater, SQLEmailStatusUpdater

# Add protocol to existing protocols section
class EmailStatusUpdater(Protocol):
    """Protocol for email status updates."""
    
    async def __call__(
        self,
        resend_email_id: str,
        event_type: str,
        event_data: dict,
    ) -> bool:
        """Update email status from webhook event."""
        ...

# Add dependency provider
def get_email_status_updater() -> EmailStatusUpdater:
    """Factory for email status updater. Override in tests."""
    return SQLEmailStatusUpdater()

# Update endpoint signature
@router.post(urls.RESEND_WEBHOOK_RECEIVING_URL)
async def resend_receiving_webhook(
    request: Request,
    verifier: WebhookVerifier = Depends(get_webhook_verifier),
    forwarder: EmailForwarder = Depends(get_email_forwarder),
    status_updater: EmailStatusUpdater = Depends(get_email_status_updater),
) -> dict[str, str]:
    """
    Handle Resend webhook events:
    - email.received: Forward emails
    - email.sent/delivered/bounced/etc: Update email logs
    
    Dependencies are injected for easy testing:
    - verifier: validates webhook signature
    - forwarder: handles email forwarding
    - status_updater: updates email delivery status
    """
    # ... existing code for signature verification and parsing ...
    
    if event_type == "email.received":
        # ... existing email forwarding logic ...
        pass
    
    elif event_type in ("email.sent", "email.delivered", "email.bounced", 
                        "email.delivery_delayed", "email.complained"):
        # Handle email delivery status events
        data = payload.get("data", {})
        email_id = data.get("email_id")
        
        if not email_id:
            logger.warning(f"Webhook {event_type} missing email_id")
            return {"status": "ignored"}
        
        # Update status using injected dependency
        success = await status_updater.update_status(
            resend_email_id=email_id,
            event_type=event_type,
            event_data=data,
        )
        
        if not success:
            logger.warning(f"No EmailLog found for resend_email_id={email_id}")
            return {"status": "not_found"}
        
        logger.info(f"Updated EmailLog for {email_id}: {event_type}")
    else:
        # Log all other events for monitoring
        logger.info(f"Received non-handled event: {event_type}")
        logger.info(f"Event data: {payload.get('data', {})}")
    
    logger.info("Webhook processing completed successfully")
    return {"status": "received"}
```

**Benefits**:
- Testable: Mock `EmailStatusUpdater` in webhook tests without database
- Reusable: Same webhook can use different updater implementations
- Clean separation: Webhook routing logic separate from status update logic
- Follows existing pattern: Same dependency injection style as `WebhookVerifier` and `EmailForwarder`

### 6. Update Write Models

**Files to modify**:
- `src/guests/features/request_invitation/write_model.py`
- Any other features that send emails

Changes:
- Extract `guest_id` and `user_id` from context
- Pass these IDs to email service methods
- Update tests to verify logging behavior

Example for `request_invitation/write_model.py`:

```python
# In _create_new_invitation()
await self.email_service.send_invitation(
    to_address=user.email,
    guest_name=f"{guest.first_name} {guest.last_name}",
    event_date=settings.event_date,
    event_location=settings.event_location,
    rsvp_url=rsvp_info.rsvp_link,
    response_deadline=settings.response_deadline,
    language=language,
    # NEW: Add context for logging
    guest_id=guest.uuid,
    user_id=user.uuid,
)
```

### 7. Skip Read Model for Email Logs

**Decision**: Do not create a read model for email logs at this time.

**Rationale**:
- Email logs are primarily for debugging and audit purposes, not for user-facing features
- Direct database queries are sufficient for admin/debugging needs
- Can add read models later if specific query patterns emerge
- Keeps initial implementation simpler and more focused

**Future consideration**: If email logs need to be exposed via API or used in complex queries, create read models then.

### 8. Testing

#### Unit Tests

**File**: `src/email_service/tests/test_email_logger.py` (new)

Test cases for email logger implementations:
- `SQLEmailLogger.log_email_attempt()` creates database record with status="pending"
- `SQLEmailLogger.log_email_success()` updates record with resend_email_id and status="sent"
- `SQLEmailLogger.log_email_failure()` updates record with error_message and status="failed"
- `NoOpEmailLogger` returns UUID without database operations

**File**: `src/email_service/tests/test_email_status_updater.py` (new)

Test cases for email status updater implementations:
- `SQLEmailStatusUpdater.update_status()` updates database record correctly for each event type
- Event type mapping (email.sent → "sent", email.bounced → "bounced", etc.)
- Bounce events store error message with bounce_type and reason
- Returns False when email log not found
- `NoOpEmailStatusUpdater` returns True without database operations

**File**: `src/email_service/tests/test_resend_service.py` (new)

Test cases for ResendEmailService with mocked EmailLogger:
- Constructor accepts EmailLogger dependency
- Constructor defaults to NoOpEmailLogger when no logger provided
- `_send()` calls `log_email_attempt()` before sending
- `_send()` calls `log_email_success()` after successful send
- `_send()` calls `log_email_failure()` on HTTP error
- All parameters passed correctly to logger (to, from, subject, bodies, type, ids, language)
- `send_invitation()` passes correct email_type="invitation"
- `send_confirmation()` passes correct email_type="confirmation"

**File**: `src/webhooks/tests/test_receiving.py` (extend existing)

Add test cases for email status events with mocked EmailStatusUpdater:
- Webhook endpoint accepts `status_updater` dependency
- Each webhook event type calls `status_updater.update_status()` with correct parameters
- Returns {"status": "not_found"} when updater returns False
- Returns {"status": "received"} when updater returns True
- Missing email_id returns {"status": "ignored"}
- Existing signature validation and email forwarding tests still pass

**File**: `src/guests/features/request_invitation/tests/test_write_model.py`

Add assertions:
- Email log created when invitation sent
- Email log has correct guest_id, user_id, email_type="invitation"

#### Integration Tests

**File**: `tests/integration/test_email_logging.py` (new)

Test full flow with real implementations:
1. Instantiate ResendEmailService with SQLEmailLogger
2. Send invitation → EmailLog created with correct data
3. Simulate webhook delivery event with SQLEmailStatusUpdater
4. Verify database state matches expectations (status updated, webhook timestamp set)

### 9. Configuration

**File**: `src/config/settings.py`

Add settings:
- `log_email_bodies: bool = True` - Toggle storing full email bodies (privacy consideration)

**Note**: Webhook configuration reuses existing setup. No new webhook URL or secret needed - the existing `/api/v1/webhooks/resend` endpoint (defined in `src/webhooks/urls.py::RESEND_WEBHOOK_RECEIVING_URL`) handles all Resend events.

### 10. Resend Dashboard Configuration

The existing Resend webhook (`https://your-domain.com/api/v1/webhooks/resend`) already receives events. Update the webhook subscription in Resend dashboard to include email delivery status events:

1. Navigate to Webhooks in Resend dashboard
2. Find existing webhook endpoint: `https://your-domain.com/api/v1/webhooks/resend`
3. Add/verify event subscriptions include:
   - `email.received` (already subscribed)
   - `email.sent`
   - `email.delivered`
   - `email.bounced`
   - `email.delivery_delayed`
   - `email.complained`

The webhook signing secret (`settings.resend_webhook_secret`) is already configured and will be used to verify all event types.

## Security Considerations

1. **Email Body Storage**: Consider privacy implications of storing full email bodies
   - Add `log_email_bodies` setting to disable if needed
   - Consider retention policy (auto-delete after N days)
   
2. **PII**: Email logs contain PII (email addresses, names)
   - Apply same access controls as Guest/User data
   - Include in GDPR deletion workflows

3. **Webhook Validation**: Always verify Svix signatures on webhook endpoints

## Future Enhancements

1. **Admin Dashboard**: View email logs, filter by status/type/date
2. **Retry Failed Emails**: API endpoint to retry emails with status="failed"
3. **Analytics**: Email open/click tracking (requires Resend analytics API)
4. **Rate Limiting**: Track and enforce email rate limits per guest/user
5. **Bulk Operations**: Log bulk email sends efficiently
6. **Email Templates Versioning**: Store template version used for each email

## Rollout Plan

1. **Phase 1**: Create migration and ORM model for `email_logs` table
2. **Phase 2**: Create `EmailLogger` abstract base class, `SQLEmailLogger`, and `NoOpEmailLogger` implementations
3. **Phase 3**: Create `EmailStatusUpdater` abstract base class, `SQLEmailStatusUpdater`, and `NoOpEmailStatusUpdater` implementations
4. **Phase 4**: Refactor `ResendEmailService` to accept `EmailLogger` dependency via constructor
5. **Phase 5**: Update dependency injection to provide `SQLEmailLogger` to `ResendEmailService`
6. **Phase 6**: Extend existing webhook handler (`/api/v1/webhooks/resend`) to inject and use `EmailStatusUpdater`
7. **Phase 7**: Update all write models to pass context parameters (guest_id, user_id) to email methods
8. **Phase 8**: Update Resend webhook subscription to include delivery status events
9. **Phase 9**: Monitor logs for 1 week, adjust as needed

## Success Criteria

- [ ] `EmailLogger` abstract base class created with clear interface
- [ ] `SQLEmailLogger` implementation persists email logs to database
- [ ] `NoOpEmailLogger` implementation available for testing
- [ ] `EmailStatusUpdater` abstract base class created with clear interface
- [ ] `SQLEmailStatusUpdater` implementation updates email status from webhooks
- [ ] `NoOpEmailStatusUpdater` implementation available for testing
- [ ] `ResendEmailService` accepts `EmailLogger` via constructor dependency injection
- [ ] Webhook handler accepts `EmailStatusUpdater` via dependency injection
- [ ] All emails logged to database with complete parameters
- [ ] Resend email ID captured for every sent email
- [ ] Webhook updates delivery status correctly via injected updater
- [ ] No performance degradation on email send or webhook processing
- [ ] 100% test coverage for new code (logger, updater, service, webhook handler)
- [ ] Email service can be easily tested with mock logger
- [ ] Webhook handler can be easily tested with mock status updater
- [ ] Failed emails easily identifiable and debuggable
