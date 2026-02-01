from sqlalchemy import select

from src.config.database import async_session_manager
from src.models.dietary import DietaryOption, DietaryType
from src.models.guest import Guest, GuestStatus


class RSVPReadService:
    """Read-only operations for RSVP."""

    @staticmethod
    async def get_rsvp_info(
        token: str,
    ) -> Guest | None:
        """
        Get guest and event info by RSVP token.
        """
        async with async_session_manager() as session:
            guest = await RSVPReadService.get_guest_by_token(session, token)
            if not guest:
                return None

            return guest

    @staticmethod
    async def get_guest_by_token(
        session,
        token: str,
    ) -> Guest | None:
        """
        Get guest by RSVP token.
        """
        result = await session.execute(select(Guest).where(Guest.rsvp_token == token))
        return result.scalar_one_or_none()


class RSVPWriteService:
    """Write operations for RSVP."""

    def __init__(self, email_service=None):
        self.email_service = email_service

    async def submit_rsvp(
        self,
        token: str,
        attending: bool,
        plus_one: bool,
        plus_one_name: str | None,
        dietary_requirements: list[dict],
    ) -> Guest:
        """
        Submit RSVP response for a guest.
        """
        async with async_session_manager() as session:
            # Use session from write operation for read (shares transaction)
            guest = await RSVPReadService.get_guest_by_token(session, token)
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

            # Send confirmation email if email_service is available
            if self.email_service:
                dietary_str = (
                    ", ".join([f"{req['requirement_type'].value}" for req in dietary_requirements])
                    if dietary_requirements
                    else "None"
                )

                await self.email_service.send_confirmation(
                    to_address=guest.email,
                    guest_name=guest.name,
                    attending="Yes" if attending else "No",
                    plus_one="Yes" if plus_one else "No",
                    dietary=dietary_str,
                    couple_names="[Couple Names]",  # TODO: Make configurable
                )

            return guest
