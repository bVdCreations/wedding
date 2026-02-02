"""RSVP models - Read and write models that return DTOs, never ORM models."""

from abc import ABC, abstractmethod

from sqlalchemy import select

from src.config.database import async_session_manager
from src.email.service import EmailService
from src.guests.dtos import GuestStatus, RSVPResponseDTO
from src.guests.repository.orm_models import DietaryOption, DietaryType
from src.guests.repository.read_models import RSVPReadModel


class RSVPWriteModel(ABC):
    @abstractmethod
    async def submit_rsvp(
        self,
        token: str,
        attending: bool,
        plus_one: bool,
        plus_one_name: str | None,
        dietary_requirements: list[dict],
    ) -> RSVPResponseDTO:
        """
        Submit RSVP response for a guest.
        Returns DTO instead of ORM model.
        """
        raise NotImplementedError


class SqlRSVPWriteModel:
    """Write operations for RSVP. Returns DTOs, never ORM models."""

    def __init__(
        self,
        read_model: RSVPReadModel,
        email_service: EmailService | None = None,
    ):
        self._email_service = email_service
        self, _read_model = read_model

    @property
    def email_service(self) -> EmailService | None:
        """Get the email service instance."""
        return self._email_service

    async def submit_rsvp(
        self,
        token: str,
        attending: bool,
        plus_one: bool,
        plus_one_name: str | None,
        dietary_requirements: list[dict],
    ) -> RSVPResponseDTO:
        """
        Submit RSVP response for a guest.
        Returns DTO instead of ORM model.
        """
        async with async_session_manager() as session:
            # Use session from write operation for read (shares transaction)
            guest = await self._read_model.get_guest_by_token(session, token)
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
