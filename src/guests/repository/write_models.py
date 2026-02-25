"""RSVP models - Read and write models that return DTOs, never ORM models."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.email.base import EmailServiceBase
from src.guests.dtos import (
    GuestStatus,
    Language,
    RSVPResponseDTO,
)
from src.guests.repository.orm_models import DietaryOption, DietaryType, Guest, RSVPInfo
from src.models.user import User

if TYPE_CHECKING:
    from src.guests.features.create_plus_one_guest.write_model import PlusOneGuestWriteModel
    from src.guests.features.update_rsvp.router import (
        FamilyMemberSubmit,
        GuestInfoSubmit,
        RSVPResponseSubmit,
    )


class RSVPWriteModel(ABC):
    @abstractmethod
    async def submit_rsvp(
        self,
        token: str,
        rsvp_data: "RSVPResponseSubmit",
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
        email_service: EmailServiceBase | None = None,
        plus_one_guest_write_model: "PlusOneGuestWriteModel | None" = None,
    ):
        self._session_overwrite = session_overwrite
        self._email_service = email_service
        self._plus_one_guest_write_model = plus_one_guest_write_model

    @property
    def email_service(self) -> EmailServiceBase | None:
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

    async def _update_guest_info(
        self, session, guest: Guest, guest_info: "GuestInfoSubmit"
    ) -> None:
        """Update guest info (first_name, last_name, phone, allergies)."""
        guest.first_name = guest_info.first_name
        guest.last_name = guest_info.last_name
        if guest_info.phone is not None:
            guest.phone = guest_info.phone
        if guest_info.allergies is not None:
            guest.allergies = guest_info.allergies

    async def _update_family_member(
        self,
        session,
        family_member_uuid: UUID,
        update_data: "FamilyMemberSubmit",
    ) -> None:
        """Update a family member's RSVP, dietary requirements, allergies, and guest info."""
        # Get family member guest
        stmt = select(Guest).where(Guest.uuid == family_member_uuid)
        result = await session.execute(stmt)
        family_member = result.scalar_one_or_none()

        if not family_member:
            raise ValueError(f"Family member with UUID {family_member_uuid} not found")

        # Get family member RSVP info
        rsvp_stmt = select(RSVPInfo).where(RSVPInfo.guest_id == family_member_uuid)
        rsvp_result = await session.execute(rsvp_stmt)
        rsvp_info = rsvp_result.scalar_one_or_none()

        if rsvp_info:
            # Update RSVP status
            rsvp_info.status = (
                GuestStatus.CONFIRMED if update_data.attending else GuestStatus.DECLINED
            )

        # Update guest info if provided
        if update_data.guest_info:
            await self._update_guest_info(session, family_member, update_data.guest_info)

        # Update allergies if provided
        if update_data.allergies is not None:
            family_member.allergies = update_data.allergies

        # Update dietary requirements
        if update_data.dietary_requirements:
            # Clear existing dietary requirements
            existing_dietary = await session.execute(
                select(DietaryOption).where(DietaryOption.guest_id == family_member_uuid)
            )
            for dietary in existing_dietary.scalars().all():
                await session.delete(dietary)

            # Add new dietary requirements
            for req in update_data.dietary_requirements:
                dietary = DietaryOption(
                    guest_id=family_member_uuid,
                    requirement_type=DietaryType(req["requirement_type"]),
                    notes=req.get("notes"),
                )
                session.add(dietary)

        await session.refresh(family_member)

    async def submit_rsvp(
        self,
        token: str,
        rsvp_data: "RSVPResponseSubmit",
    ) -> RSVPResponseDTO:
        """
        Submit RSVP response for a guest.
        Returns DTO instead of ORM model.
        Supports updating guest info and family member RSVP/dietary.
        """
        attending = rsvp_data.attending
        plus_one_details = rsvp_data.plus_one_details
        dietary_requirements = rsvp_data.dietary_requirements
        guest_info = rsvp_data.guest_info
        family_member_updates = rsvp_data.family_member_updates

        async with async_session_manager(session_overwrite=self._session_overwrite) as session:
            if self._plus_one_guest_write_model:
                self._plus_one_guest_write_model.set_session_overwrite(session)
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
                    # Handle both dict and Pydantic model
                    if isinstance(req, dict):
                        req_type = req["requirement_type"]
                        notes = req.get("notes")
                    else:
                        req_type = req.requirement_type
                        notes = req.notes
                    dietary = DietaryOption(
                        guest_id=guest.uuid,
                        requirement_type=DietaryType(req_type),
                        notes=notes,
                    )
                    session.add(dietary)

            # Update guest info if provided
            if guest_info:
                await self._update_guest_info(session, guest, guest_info)

            # Update main guest allergies if provided
            if rsvp_data.allergies is not None:
                guest.allergies = rsvp_data.allergies

            await session.refresh(guest)

            # Create plus-one guest if details provided
            if attending and plus_one_details and self._plus_one_guest_write_model:
                (
                    _,
                    plus_one_guest_uuid,
                ) = await self._plus_one_guest_write_model.create_plus_one_guest(
                    original_guest_id=guest.uuid,
                    plus_one_data=plus_one_details,
                )
                # Set bring_a_plus_one_id to the plus-one guest's UUID
                guest.bring_a_plus_one_id = plus_one_guest_uuid
                # Save allergies for plus one if provided
                plus_one_allergies = getattr(plus_one_details, "allergies", None)
                if plus_one_allergies:
                    po_stmt = select(Guest).where(Guest.uuid == plus_one_guest_uuid)
                    po_result = await session.execute(po_stmt)
                    po_guest = po_result.scalar_one_or_none()
                    if po_guest:
                        po_guest.allergies = plus_one_allergies

            # Update family members if provided
            if family_member_updates:
                for member_id, update_data in family_member_updates.items():
                    await self._update_family_member(session, UUID(member_id), update_data)

            # Build response message
            message = (
                "Thank you for confirming your attendance!"
                if attending
                else "We're sorry you can't make it. Your response has been recorded."
            )

            # Send confirmation email if email_service is available
            if self._email_service:
                # Handle both dict and Pydantic model for dietary_requirements
                if dietary_requirements:
                    dietary_list = []
                    for req in dietary_requirements:
                        if isinstance(req, dict):
                            dietary_list.append(req["requirement_type"])
                        else:
                            dietary_list.append(req.requirement_type)
                    dietary_str = ", ".join(dietary_list)
                else:
                    dietary_str = "None"

                user_email = await self._get_user_email(session, guest.user_id)
                guest_name = f"{guest.first_name} {guest.last_name}"

                # Get guest's preferred language
                preferred_language = getattr(guest, "preferred_language", Language.EN)

                await self._email_service.send_confirmation(
                    to_address=user_email,
                    guest_name=guest_name,
                    attending="Yes" if attending else "No",
                    dietary=dietary_str,
                    language=preferred_language,
                )

            # Return DTO instead of ORM model
            return RSVPResponseDTO(
                message=message,
                attending=attending,
                status=rsvp_info.status,
            )
