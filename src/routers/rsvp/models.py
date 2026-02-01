"""RSVP models - Read and write models that return DTOs, never ORM models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select

from src.config.database import async_session_manager
from src.email.service import EmailService
from src.models.dietary import DietaryOption, DietaryType
from src.models.guest import Guest, GuestStatus


# =============================================================================
# DTOs (Data Transfer Objects)
# =============================================================================

@dataclass(frozen=True)
class RSVPInfoDTO:
    """DTO for RSVP page info returned by read model."""
    token: str
    name: str
    event_name: str
    event_date: str
    event_location: str
    status: GuestStatus
    is_plus_one: bool
    plus_one_name: Optional[str] = None


@dataclass(frozen=True)
class GuestDTO:
    """DTO for guest data."""
    id: UUID
    name: str
    status: GuestStatus
    is_plus_one: bool
    plus_one_name: Optional[str]
    email: str


@dataclass(frozen=True)
class RSVPResponseDTO:
    """DTO for RSVP response."""
    message: str
    attending: bool
    status: GuestStatus


# =============================================================================
# Read Model
# =============================================================================

class RSVPReadModel:
    """Read-only operations for RSVP. Returns DTOs, never ORM models."""

    @staticmethod
    async def get_rsvp_info(token: str) -> Optional[RSVPInfoDTO]:
        """
        Get guest and event info by RSVP token.
        Returns None if guest not found.
        """
        async with async_session_manager() as session:
            guest = await RSVPReadModel._get_guest_by_token(session, token)
            if not guest:
                return None

            # Return DTO instead of ORM model
            return RSVPInfoDTO(
                token=token,
                name=guest.name,
                event_name="Wedding Celebration",  # TODO: Make configurable
                event_date="October 15, 2026 at 3:00 PM",  # TODO: Make configurable
                event_location="Grand Ballroom",  # TODO: Make configurable
                status=guest.status,
                is_plus_one=guest.is_plus_one,
                plus_one_name=guest.plus_one_name,
            )

    @staticmethod
    async def get_guest_by_token(session, token: str) -> Optional[Guest]:
        """
        Get guest by RSVP token.
        Internal method - still returns ORM for session management.
        """
        result = await session.execute(select(Guest).where(Guest.rsvp_token == token))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_guest_dto(token: str) -> Optional[GuestDTO]:
        """
        Get guest as DTO by RSVP token.
        """
        async with async_session_manager() as session:
            guest = await RSVPReadModel._get_guest_by_token(session, token)
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


# =============================================================================
# Write Model
# =============================================================================

class RSVPWriteModel:
    """Write operations for RSVP. Returns DTOs, never ORM models."""

    def __init__(self, email_service: Optional[EmailService] = None):
        self._email_service = email_service

    @property
    def email_service(self) -> Optional[EmailService]:
        """Get the email service instance."""
        return self._email_service

    async def submit_rsvp(
        self,
        token: str,
        attending: bool,
        plus_one: bool,
        plus_one_name: Optional[str],
        dietary_requirements: list[dict],
    ) -> RSVPResponseDTO:
        """
        Submit RSVP response for a guest.
        Returns DTO instead of ORM model.
        """
        async with async_session_manager() as session:
            # Use session from write operation for read (shares transaction)
            guest = await RSVPReadModel.get_guest_by_token(session, token)
            if not guest:
                raise ValueError("Invalid RSVP token")

            # Update guest status
            guest.status = GuestStatus.CONFIRMED if attending else GuestStatus.DECLINED
            guest.is_plus_one = plus_one
            guest.plus_one_name = plus_one_name if attending else None

            # Clear existing dietary requirements
            existing_dietary = await session.execute(
                select(DietaryOption).where(DietaryOption.guest_id == guest.id)
            )
            for dietary in existing_dietary.scalars().all():
                await session.delete(dietary)

            # Add new dietary requirements if attending
            if attending and dietary_requirements:
                for req in dietary_requirements:
                    dietary = DietaryOption(
                        guest_id=guest.id,
                        requirement_type=DietaryType(req["requirement_type"]),
                        notes=req.get("notes"),
                    )
                    session.add(dietary)

            await session.refresh(guest)

            # Build response message
            message = (
                "Thank you for confirming your attendance!"
                if attending
                else "We're sorry you can't make it. Your response has been recorded."
            )

            # Send confirmation email if email_service is available
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
                    couple_names="[Couple Names]",  # TODO: Make configurable
                )

            # Return DTO instead of ORM model
            return RSVPResponseDTO(
                message=message,
                attending=attending,
                status=guest.status,
            )
