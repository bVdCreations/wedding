"""In-memory models for testing - no database required."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from src.email.service import EmailService
from src.models.dietary import DietaryType
from src.models.guest import GuestStatus
from src.routers.rsvp.models import (
    GuestDTO,
    RSVPInfoDTO,
    RSVPReadModel,
    RSVPResponseDTO,
    RSVPWriteModel,
)


# =============================================================================
# In-Memory Storage
# =============================================================================

@dataclass
class GuestStorage:
    """In-memory storage for guests."""
    token: str
    name: str
    email: str
    status: GuestStatus = GuestStatus.PENDING
    is_plus_one: bool = False
    plus_one_name: Optional[str] = None
    dietary_requirements: list = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)


class InMemoryEmailService:
    """In-memory email service for testing."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        plus_one: str,
        dietary: str,
        couple_names: str,
    ):
        """Record email instead of sending."""
        self.sent_emails.append({
            "to_address": to_address,
            "guest_name": guest_name,
            "attending": attending,
            "plus_one": plus_one,
            "dietary": dietary,
            "couple_names": couple_names,
        })


# =============================================================================
# In-Memory Read Model
# =============================================================================

class InMemoryRSVPReadModel(RSVPReadModel):
    """In-memory read model for testing."""

    def __init__(self, guests: list[GuestStorage] = None):
        self._guests: dict[str, GuestStorage] = {}
        if guests:
            for guest in guests:
                self._guests[guest.token] = guest

    async def get_rsvp_info(self, token: str) -> Optional[RSVPInfoDTO]:
        """Get RSVP info from in-memory storage."""
        guest = self._guests.get(token)
        if not guest:
            return None

        return RSVPInfoDTO(
            token=guest.token,
            name=guest.name,
            event_name="Wedding Celebration",  # Match the real model
            event_date="October 15, 2026 at 3:00 PM",
            event_location="Grand Ballroom",
            status=guest.status,
            is_plus_one=guest.is_plus_one,
            plus_one_name=guest.plus_one_name,
        )

    async def get_guest_dto(self, token: str) -> Optional[GuestDTO]:
        """Get guest DTO from in-memory storage."""
        guest = self._guests.get(token)
        if not guest:
            return None

        return GuestDTO(
            id=guest.id,
            name=guest.name,
            status=guest.status,
            is_plus_one=guest.is_plus_one,
            plus_one_name=guest.plus_one_name,
            email=guest.email,
        )

    def add_guest(self, guest: GuestStorage):
        """Add a guest to the in-memory storage."""
        self._guests[guest.token] = guest

    def update_guest(self, token: str, **kwargs):
        """Update a guest in the in-memory storage."""
        guest = self._guests.get(token)
        if guest:
            for key, value in kwargs.items():
                setattr(guest, key, value)


# =============================================================================
# In-Memory Write Model
# =============================================================================

class InMemoryRSVPWriteModel(RSVPWriteModel):
    """In-memory write model for testing."""

    def __init__(
        self,
        read_model: InMemoryRSVPReadModel,
        email_service: Optional[InMemoryEmailService] = None,
    ):
        super().__init__(email_service=email_service)
        self._read_model = read_model

    async def submit_rsvp(
        self,
        token: str,
        attending: bool,
        plus_one: bool,
        plus_one_name: Optional[str],
        dietary_requirements: list[dict],
    ) -> RSVPResponseDTO:
        """Submit RSVP to in-memory storage."""
        guest = self._read_model._guests.get(token)
        if not guest:
            raise ValueError("Invalid RSVP token")

        # Update guest status
        guest.status = GuestStatus.CONFIRMED if attending else GuestStatus.DECLINED
        guest.is_plus_one = plus_one
        guest.plus_one_name = plus_one_name if attending else None

        # Update dietary requirements if attending
        if attending:
            guest.dietary_requirements = dietary_requirements
        else:
            guest.dietary_requirements = []

        # Build response message
        message = (
            "Thank you for confirming your attendance!"
            if attending
            else "We're sorry you can't make it. Your response has been recorded."
        )

        # Record email if email service is available
        if self._email_service:
            dietary_str = (
                ", ".join([f"{req['requirement_type'].value}" for req in dietary_requirements])
                if dietary_requirements
                else "None"
            )

            await self._email_service.send_confirmation(
                to_address=guest.email,
                guest_name=guest.name,
                attending="Yes" if attending else "No",
                plus_one="Yes" if plus_one else "No",
                dietary=dietary_str,
                couple_names="[Couple Names]",
            )

        return RSVPResponseDTO(
            message=message,
            attending=attending,
            status=guest.status,
        )


# =============================================================================
# Factory Functions for Tests
# =============================================================================

def create_test_guest(
    token: str = "test-token-12345",
    name: str = "John Doe",
    email: str = "john@example.com",
    status: GuestStatus = GuestStatus.PENDING,
    is_plus_one: bool = False,
    plus_one_name: Optional[str] = None,
) -> GuestStorage:
    """Factory function to create test guests."""
    return GuestStorage(
        token=token,
        name=name,
        email=email,
        status=status,
        is_plus_one=is_plus_one,
        plus_one_name=plus_one_name,
    )


def create_test_read_model(guests: list[GuestStorage] = None) -> InMemoryRSVPReadModel:
    """Factory function to create in-memory read model."""
    return InMemoryRSVPReadModel(guests=guests)


def create_test_write_model(
    read_model: InMemoryRSVPReadModel,
    email_service: Optional[InMemoryEmailService] = None,
) -> InMemoryRSVPWriteModel:
    """Factory function to create in-memory write model."""
    return InMemoryRSVPWriteModel(
        read_model=read_model,
        email_service=email_service,
    )


def create_test_email_service() -> InMemoryEmailService:
    """Factory function to create in-memory email service."""
    return InMemoryEmailService()
