# Plan: Implement Resend Email Service

## Understanding the Current State

After reviewing the codebase, I found:
- **Current Email Service**: Uses raw SMTP via `smtplib` in `src/email/service.py`
- **Email Templates**: Multi-language templates (EN, ES, NL) in `src/email/templates.py`
- **Configuration**: SMTP settings in `src/config/settings.py` with environment variables
- **Development Setup**: Mailhog already configured in `docker-compose.yml`
- **Environment**: Uses `ENVIRONMENT` setting to distinguish dev/prod

## User Request

Implement email sending with Resend:
- **Development**: Send emails to Mailhog (already available)
- **Production**: Send emails via Resend API

## Implementation Plan

### Step 1: Add Resend SDK Dependency

**File**: `pyproject.toml`

Add to `dependencies`:
```python
"resend>=2.0.0",
```

### Step 2: Update Settings for Resend

**File**: `src/config/settings.py`

Add new Resend-specific settings:
```python
# Resend Email (Production)
use_resend: bool = False  # Toggle between SMTP and Resend
resend_api_key: str = ""  # RESEND_API_KEY for production

# Override from address for Resend (must be verified domain)
resend_from_address: str = ""
```

### Step 3: Create Resend Email Service

**File**: `src/email/resend_service.py` (new)

Create a new service using the Resend Python SDK:

```python
import resend
from src.config.settings import settings
from src.email.templates import EmailTemplates
from src.guests.dtos import Language

class ResendEmailService:
    def __init__(self):
        resend.api_key = settings.resend_api_key
        self.from_address = settings.resend_from_address or settings.emails_from

    async def send_invitation(self, to_address: str, guest_name: str, event_date: str, event_location: str, rsvp_url: str, response_deadline: str, language: Language = Language.EN) -> None:
        subject, html_template, text_template = EmailTemplates.get_invitation_templates(language)

        html_body = html_template.format(...)
        text_body = text_template.format(...)

        params: resend.Emails.SendParams = {
            "from": self.from_address,
            "to": [to_address],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        }
        resend.Emails.send(params)

    async def send_confirmation(self, to_address: str, guest_name: str, attending: str, dietary: str, language: Language = Language.EN) -> None:
        # Similar implementation for confirmation emails
        pass
```

### Step 4: Update Main Email Service with Factory Pattern

**File**: `src/email/service.py`

Refactor to support both SMTP and Resend:

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config.settings import settings
from src.email.templates import EmailTemplates
from src.guests.dtos import Language

# Import Resend service if available
try:
    from src.email.resend_service import ResendEmailService
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False


class EmailService:
    def __init__(self):
        if settings.use_resend and RESEND_AVAILABLE:
            self._service = ResendEmailService()
            self._use_resend = True
        else:
            self._use_resend = False
            self.host = settings.smtp_host
            self.port = settings.smtp_port
            self.username = settings.smtp_user
            self.password = settings.smtp_password
            self.from_address = settings.emails_from

    # Delegate methods to appropriate service
    async def send_invitation(self, to_address: str, guest_name: str, event_date: str, event_location: str, rsvp_url: str, response_deadline: str, language: Language = Language.EN) -> None:
        if self._use_resend:
            return await self._service.send_invitation(to_address, guest_name, event_date, event_location, rsvp_url, response_deadline, language)
        # Original SMTP implementation...

    async def send_confirmation(self, to_address: str, guest_name: str, attending: str, dietary: str, language: Language = Language.EN) -> None:
        if self._use_resend:
            return await self._service.send_confirmation(to_address, guest_name, attending, dietary, language)
        # Original SMTP implementation...
```

### Step 5: Update Docker Compose for Development

**File**: `docker-compose.yml`

Update API service environment to disable Resend:
```yaml
api:
  environment:
    # ... existing settings ...
    USE_RESEND: "false"  # Development: use Mailhog via SMTP
    SMTP_HOST: mailhog
    SMTP_PORT: 1025
```

### Step 6: Environment Variables for Production

**File**: `.envrc` (or create production environment config)

For production deployment:
```bash
# Production email settings
USE_RESEND=true
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_ADDRESS=wedding@yourdomain.com

# Disable SMTP in production
SMTP_HOST=
SMTP_PORT=
```

### Step 7: Update Existing SMTP Settings

**File**: `src/config/settings.py`

Mark SMTP settings as optional for production:
```python
# Email (SMTP - for development with Mailhog)
smtp_host: str = "localhost"
smtp_port: int = 1025
smtp_user: str = ""  # Empty in production when using Resend
smtp_password: str = ""  # Empty in production when using Resend
emails_from: str = "wedding@example.com"
```

### Step 8: Error Handling and Logging

**File**: `src/email/service.py`

Add proper error handling:
```python
import structlog

logger = structlog.get_logger()

class EmailService:
    async def _send_with_resend(self, params: dict) -> None:
        try:
            result = resend.Emails.send(params)
            logger.info("Email sent via Resend", email_id=result.get("id"))
        except Exception as e:
            logger.error("Failed to send email via Resend", error=str(e))
            raise
```

### Step 9: Optional - Add Email Logging/Debugging

**File**: `src/email/service.py`

For development, log email contents:
```python
if settings.DEBUG and not self._use_resend:
    logger.debug("Email sent (development)", to=to_address, subject=subject)
```

### Step 10: Test Email Sending

**Files to create**: `src/email/tests/`

Create tests for both Resend and SMTP paths:
- Test Resend service (mocked)
- Test SMTP fallback (existing)
- Test factory pattern selection
- Test error handling

## Files to Create

1. `src/email/resend_service.py` - New Resend email service

## Files to Modify

### Backend
1. `pyproject.toml` - Add Resend dependency
2. `src/config/settings.py` - Add Resend settings
3. `src/email/service.py` - Refactor with factory pattern
4. `docker-compose.yml` - Document environment variables

### Documentation
5. `.envrc` - Add production environment variables
6. `README.md` - Update email configuration section

## Environment Variable Summary

### Development (Mailhog)
```
USE_RESEND=false
SMTP_HOST=mailhog
SMTP_PORT=1025
EMAILS_FROM=wedding@example.com
```

### Production (Resend)
```
USE_RESEND=true
RESEND_API_KEY=re_your_api_key
RESEND_FROM_ADDRESS=wedding@yourdomain.com
# SMTP settings can be empty or unset
```

## Testing Checklist

- [ ] Resend SDK installed and imported
- [ ] Development mode uses Mailhog via SMTP
- [ ] Production mode uses Resend API
- [ ] Email templates render correctly with Resend
- [ ] Error handling works for both paths
- [ ] Logging captures email sends
- [ ] All email methods (invitation, confirmation) work with both backends
- [ ] Environment variables properly configured

## Resend API Key Setup (Production)

1. Sign up at https://resend.com
2. Add and verify your domain (required for production sending)
3. Create an API key in the Resend dashboard
4. Add the API key to your production environment variables
5. Configure the `RESEND_FROM_ADDRESS` to use your verified domain

## Notes

- Resend requires a verified domain for production email sending
- For testing, you can use the default `onboarding@resend.dev` sender
- Consider adding idempotency keys for important emails
- Resend provides better deliverability and tracking than raw SMTP