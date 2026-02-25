"""
Domain events for the wedding RSVP system.

This module defines domain events that can be used for:
- Event sourcing
- Message bus integration
- Audit logging
- Email notifications
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DomainEvent:
    """Base domain event."""

    timestamp: datetime = None
    event_type: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class GuestCreatedEvent(DomainEvent):
    """Event fired when a new guest is created."""

    guest_id: str
    guest_name: str
    guest_email: str
    event_id: str

    def __post_init__(self):
        super().__post_init__()
        self.event_type = "guest.created"


@dataclass
class GuestInvitedEvent(DomainEvent):
    """Event fired when an invitation is sent to a guest."""

    guest_id: str
    guest_email: str
    rsvp_token: str

    def __post_init__(self):
        super().__post_init__()
        self.event_type = "guest.invited"


@dataclass
class RSVPResponseEvent(DomainEvent):
    """Event fired when a guest responds to an invitation."""

    guest_id: str
    guest_name: str
    attending: bool
    plus_one: bool
    plus_one_name: str | None
    dietary_requirements: list[str]

    def __post_init__(self):
        super().__post_init__()
        self.event_type = "guest.rsvp_response"
