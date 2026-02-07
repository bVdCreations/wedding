import abc

from sqlalchemy import select

from src.config.database import async_session_manager
from src.guests.dtos import DietaryType, GuestStatus, RSVPInfoDTO
from src.guests.repository.orm_models import DietaryOption, Guest, RSVPInfo
from src.models.user import User


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

            # Get plus-one guest details if this guest is bringing one
            plus_one_email = None
            plus_one_first_name = None
            plus_one_last_name = None
            if guest and guest.bring_a_plus_one_id:
                plus_one_stmt = select(Guest).where(Guest.uuid == guest.bring_a_plus_one_id)
                plus_one_result = await session.execute(plus_one_stmt)
                plus_one_guest = plus_one_result.scalar_one_or_none()
                if plus_one_guest:
                    plus_one_first_name = plus_one_guest.first_name
                    plus_one_last_name = plus_one_guest.last_name
                    # Get plus-one's email from User table
                    user_stmt = select(User).where(User.uuid == plus_one_guest.user_id)
                    user_result = await session.execute(user_stmt)
                    plus_one_user = user_result.scalar_one_or_none()
                    if plus_one_user:
                        plus_one_email = plus_one_user.email

            return RSVPInfoDTO(
                token=rsvp_info.rsvp_token,
                name=name,
                status=rsvp_info.status,
                plus_one_of_id=guest.plus_one_of_id if guest else None,
                plus_one_email=plus_one_email,
                plus_one_first_name=plus_one_first_name,
                plus_one_last_name=plus_one_last_name,
                attending=attending,
                dietary_requirements=dietary_requirements,
            )
