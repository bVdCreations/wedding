"""RSVP models - Read and write models that return DTOs, never ORM models."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.email.service import EmailService
from src.guests.dtos import GuestStatus, PlusOneDTO, RSVPResponseDTO
from src.guests.repository.orm_models import DietaryOption, DietaryType, Guest, RSVPInfo
from src.models.user import User

if TYPE_CHECKING:
    from src.guests.features.create_plus_one_guest.write_model import PlusOneGuestWriteModel


class RSVPWriteModel(ABC):
    @abstractmethod
    async def submit_rsvp(
        self,
        token: str,
        attending: bool,
        plus_one_details: PlusOneDTO | None,
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
        session_overwrite: AsyncSession | None = None,
        email_service: EmailService | None = None,
        plus_one_guest_write_model: "PlusOneGuestWriteModel | None" = None,
    ):
        self._session_overwrite = session_overwrite
        self._email_service = email_service
        self._plus_one_guest_write_model = plus_one_guest_write_model

    @property
    def email_service(self) -> EmailService | None:
        """Get the email service instance."""
        return self._email_service

    async def _get_guest_by_token(self, session, token: str) -> Guest | None:
        """Get a guest by RSVP token."""
        stmt = (
            select(Guest)
            .join(RSVPInfo, Guest.uuid == RSVPInfo.guest_id)
            .where(RSVPInfo.rsvp_token == token)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_email(self, session, user_id) -> str:
        """Get user email by user_id."""
        stmt = select(User).where(User.uuid == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.email if user else ""

    async def submit_rsvp(
        self,
        token: str,
        attending: bool,
        plus_one_details: PlusOneDTO | None,
        dietary_requirements: list[dict],
    ) -> RSVPResponseDTO:
        """
        Submit RSVP response for a guest.
        Returns DTO instead of ORM model.
        """
        async with async_session_manager(session_overwrite=self._session_overwrite) as session:
            if self._plus_one_guest_write_model:
                self._plus_one_guest_write_model.session_overwrite(session)
                self._plus_one_guest_write_model.set_email_service(self._email_service)
            guest = await self._get_guest_by_token(session, token)
            if not guest:
                raise ValueError("Invalid RSVP token")

            # Get RSVP info to update status
            rsvp_stmt = select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
            rsvp_result = await session.execute(rsvp_stmt)
            rsvp_info = rsvp_result.scalar_one_or_none()

            # Update RSVP status
            rsvp_info.status = GuestStatus.CONFIRMED if attending else GuestStatus.DECLINED

            # Clear bring_a_plus_one_id if not attending
            if not attending:
                guest.bring_a_plus_one_id = None

            # Clear existing dietary requirements
            existing_dietary = await session.execute(
                select(DietaryOption).where(DietaryOption.guest_id == guest.uuid)
            )
            for dietary in existing_dietary.scalars().all():
                await session.delete(dietary)

            # Add new dietary requirements if attending
            if attending and dietary_requirements:
                for req in dietary_requirements:
                    dietary = DietaryOption(
                        guest_id=guest.uuid,
                        requirement_type=DietaryType(req["requirement_type"]),
                        notes=req.get("notes"),
                    )
                    session.add(dietary)

            await session.refresh(guest)

            # Create plus-one guest if details provided
            if attending and plus_one_details and self._plus_one_guest_write_model:
                _, plus_one_guest_uuid = await self._plus_one_guest_write_model.create_plus_one_guest(
                    original_guest_id=guest.uuid,
                    plus_one_data=plus_one_details,
                )
                # Set bring_a_plus_one_id to the plus-one guest's UUID
                guest.bring_a_plus_one_id = plus_one_guest_uuid

            # Build response message
            message = (
                "Thank you for confirming your attendance!"
                if attending
                else "We're sorry you can't make it. Your response has been recorded."
            )

            # Send confirmation email if email_service is available
            if self._email_service:
                dietary_str = (
                    ", ".join([req["requirement_type"] for req in dietary_requirements])
                    if dietary_requirements
                    else "None"
                )

                user_email = await self._get_user_email(session, guest.user_id)
                guest_name = f"{guest.first_name} {guest.last_name}"

                await self._email_service.send_confirmation(
                    to_address=user_email,
                    guest_name=guest_name,
                    attending="Yes" if attending else "No",
                    dietary=dietary_str,
                )

            # Return DTO instead of ORM model
            return RSVPResponseDTO(
                message=message,
                attending=attending,
                status=rsvp_info.status,
            )
