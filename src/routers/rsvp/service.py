from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.guest import Guest, GuestStatus
from src.models.dietary import DietaryOption, DietaryType
from src.models.event import Event
from src.email.service import email_service
from src.config.settings import settings


class RSVPService:
    @staticmethod
    async def get_rsvp_info(
        db: AsyncSession,
        token: str,
    ) -> tuple[Optional[Guest], Optional[Event]]:
        """
        Get guest and event info by RSVP token.
        """
        guest_result = await db.execute(select(Guest).where(Guest.rsvp_token == token))
        guest = guest_result.scalar_one_or_none()

        if not guest:
            return None, None

        event_result = await db.execute(select(Event).where(Event.id == guest.event_id))
        event = event_result.scalar_one_or_none()

        return guest, event

    @staticmethod
    async def submit_rsvp(
        db: AsyncSession,
        token: str,
        attending: bool,
        plus_one: bool,
        plus_one_name: Optional[str],
        dietary_requirements: list[dict],
    ) -> Guest:
        """
        Submit RSVP response for a guest.
        """
        guest = await RSVPService.get_guest_by_token(db, token)
        if not guest:
            raise ValueError("Invalid RSVP token")

        # Update guest status
        guest.status = GuestStatus.CONIRMED if attending else GuestStatus.DECLINED
        guest.is_plus_one = plus_one
        guest.plus_one_name = plus_one_name if attending else None

        # Clear existing dietary requirements
        existing_dietary = await db.execute(
            select(DietaryOption).where(DietaryOption.guest_id == guest.id)
        )
        for dietary in existing_dietary.scalars().all():
            await db.delete(dietary)

        # Add new dietary requirements if attending
        if attending and dietary_requirements:
            for req in dietary_requirements:
                dietary = DietaryOption(
                    guest_id=guest.id,
                    requirement_type=DietaryType(req["requirement_type"]),
                    notes=req.get("notes"),
                )
                db.add(dietary)

        await db.commit()
        await db.refresh(guest)

        # Send confirmation email
        event_result = await db.execute(select(Event).where(Event.id == guest.event_id))
        event = event_result.scalar_one_or_none()

        if event:
            dietary_str = (
                ", ".join([f"{req['requirement_type'].value}" for req in dietary_requirements])
                if dietary_requirements
                else "None"
            )

            await email_service.send_confirmation(
                to_address=guest.email,
                guest_name=guest.name,
                attending="Yes" if attending else "No",
                plus_one="Yes" if plus_one else "No",
                dietary=dietary_str,
                couple_names="[Couple Names]",  # TODO: Make configurable
            )

        return guest

    @staticmethod
    async def get_guest_by_token(
        db: AsyncSession,
        token: str,
    ) -> Optional[Guest]:
        """
        Get guest by RSVP token.
        """
        result = await db.execute(select(Guest).where(Guest.rsvp_token == token))
        return result.scalar_one_or_none()
