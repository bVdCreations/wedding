# Plan: Add Tests for RSVP Deadline in Invitation Emails

## Summary
Write unit tests to verify that the `rsvp_deadline` configuration value is correctly included in all invitation email templates (English, Spanish, Dutch - both regular and plus-one invitations).

## Current Situation
- No existing tests for `src/email_service/` module (no test directory exists)
- The `rsvp_deadline` is pulled from `WeddingConfig` and inserted into templates via `EmailTemplates`
- Tests in this project use pytest with AsyncMock for email service mocking

## Files to Create

### 1. `src/email_service/tests/__init__.py`
- Empty file for pytest discovery

### 2. `src/email_service/tests/test_template_builder.py`
- Test file for email template builder

## Test Cases to Add

| Test Name | Description |
|-----------|-------------|
| `test_invitation_template_contains_rsvp_deadline_en` | Verify English HTML/text invitation templates contain `rsvp_deadline` |
| `test_invitation_template_contains_rsvp_deadline_es` | Verify Spanish invitation templates contain `rsvp_deadline` |
| `test_invitation_template_contains_rsvp_deadline_nl` | Verify Dutch invitation templates contain `rsvp_deadline` |
| `test_plus_one_invitation_template_contains_rsvp_deadline_en` | Verify English plus-one templates contain `rsvp_deadline` |
| `test_plus_one_invitation_template_contains_rsvp_deadline_es` | Verify Spanish plus-one templates contain `rsvp_deadline` |
| `test_plus_one_invitation_template_contains_rsvp_deadline_nl` | Verify Dutch plus-one templates contain `rsvp_deadline` |
| `test_rsvp_deadline_config_value_used_in_template` | Verify changing `WeddingConfig.rsvp_deadline` reflects in generated email |

## Test Implementation Approach

```python
import pytest
from src.email_service.template_builder import EmailTemplates
from src.email_service.config import WeddingConfig
from src.guests.dtos import Language

def test_rsvp_deadline_config_value_used_in_template():
    """Verify rsvp_deadline from config is used in invitation templates."""
    config = WeddingConfig()
    templates = EmailTemplates()
    
    content = templates.get_invitation_templates(
        language=Language.EN,
        guest_name="Test Guest",
        rsvp_url="https://example.com/rsvp"
    )
    
    assert config.rsvp_deadline in content.html_body
    assert config.rsvp_deadline in content.text_body
```

## Notes
- These tests will validate that the deadline change (from "September 7, 2026" to "March 31, 2026") works correctly once implemented
- Tests verify the integration between `WeddingConfig` and `EmailTemplates`
- No test database or mocking required - tests use the actual config and template builder