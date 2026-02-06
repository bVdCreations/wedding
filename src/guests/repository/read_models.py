import abc

from sqlalchemy import select

from src.config.database import async_session_manager
from src.guests.dtos import DietaryType, GuestStatus, RSVPInfoDTO
from src.guests.repository.orm_models import DietaryOption, Guest, RSVPInfo


class RSVPReadModel(abc.ABC):
    @abc.abstractmethod
    async def get_rsvp_info(self, token: str) -> RSVPInfoDTO | None:
        """
        Get RSVP info by token.
        Returns RSVPInfoDTO with prefill data (attending, dietary_requirements).
        """
        raise NotImplementedError


class SqlRSVPReadModel(RSVPReadModel):
    """SQL implementation of RSVP read model."""

    async def get_rsvp_info(self, token: str) -> RSVPInfoDTO | None:
        """
        Get RSVP info by token.
        Includes dietary requirements and attending status for form prefill.
        """
        async with async_session_manager() as session:
            # Get RSVP info
            rsvp_stmt = (
                select(RSVPInfo)
                .join(Guest, RSVPInfo.guest_id == Guest.uuid)
                .where(RSVPInfo.rsvp_token == token)
            )
            rsvp_result = await session.execute(rsvp_stmt)
            rsvp_info = rsvp_result.scalar_one_or_none()

            if not rsvp_info:
                return None

            # Map status to attending boolean
            if rsvp_info.status == GuestStatus.CONFIRMED:
                attending = True
            elif rsvp_info.status == GuestStatus.DECLINED:
                attending = False
            else:
                attending = None  # PENDING

            # Get dietary requirements
            dietary_stmt = select(DietaryOption).where(
                DietaryOption.guest_id == rsvp_info.guest_id
            )
            dietary_result = await session.execute(dietary_stmt)
            dietary_options = dietary_result.scalars().all()

            dietary_requirements = [
                {
                    "requirement_type": option.requirement_type.value,
                    "notes": option.notes,
                }
                for option in dietary_options
            ]

            # Build name from guest
            guest_stmt = select(Guest).where(Guest.uuid == rsvp_info.guest_id)
            guest_result = await session.execute(guest_stmt)
            guest = guest_result.scalar_one_or_none()

            name = f"{guest.first_name} {guest.last_name}" if guest else "Guest"

            return RSVPInfoDTO(
                token=rsvp_info.rsvp_token,
                name=name,
                status=rsvp_info.status,
                is_plus_one=guest.is_plus_one if guest else False,
                plus_one_name=guest.plus_one_name if guest else None,
                attending=attending,
                dietary_requirements=dietary_requirements,
            )
