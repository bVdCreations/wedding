import abc

from sqlalchemy import select

from src.config.database import async_session_manager
from src.guests.dtos import DietaryType, FamilyMemberDTO, GuestStatus, RSVPInfoDTO
from src.guests.repository.orm_models import DietaryOption, Family, Guest, RSVPInfo
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
        Includes dietary requirements, attending status, and family members for form prefill.
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

            # Get dietary requirements for current guest
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

            # Get guest info
            guest_stmt = select(Guest).where(Guest.uuid == rsvp_info.guest_id)
            guest_result = await session.execute(guest_stmt)
            guest = guest_result.scalar_one_or_none()

            if not guest:
                return None

            # Get family members if guest is in a family
            family_members: list[FamilyMemberDTO] = []
            family_id = None
            if guest.family_id:
                family_id = guest.family_id
                # Get all family members except current guest
                family_stmt = (
                    select(Guest)
                    .where(Guest.family_id == guest.family_id)
                    .where(Guest.uuid != guest.uuid)
                )
                family_result = await session.execute(family_stmt)
                family_guests = family_result.scalars().all()

                for family_guest in family_guests:
                    # Get RSVP status for family member
                    family_rsvp_stmt = select(RSVPInfo).where(
                        RSVPInfo.guest_id == family_guest.uuid
                    )
                    family_rsvp_result = await session.execute(family_rsvp_stmt)
                    family_rsvp_info = family_rsvp_result.scalar_one_or_none()

                    family_rsvp_status = (
                        family_rsvp_info.status if family_rsvp_info else None
                    )

                    # Get dietary requirements for family member
                    family_dietary_stmt = select(DietaryOption).where(
                        DietaryOption.guest_id == family_guest.uuid
                    )
                    family_dietary_result = await session.execute(family_dietary_stmt)
                    family_dietary_options = family_dietary_result.scalars().all()

                    family_dietary_requirements = [
                        {
                            "requirement_type": option.requirement_type.value,
                            "notes": option.notes,
                        }
                        for option in family_dietary_options
                    ]

                    family_members.append(
                        FamilyMemberDTO.from_guest(
                            guest=family_guest,
                            rsvp_status=family_rsvp_status,
                            dietary_requirements=family_dietary_requirements,
                        )
                    )

            # Get plus-one guest details if this guest is bringing one
            plus_one_email = None
            plus_one_first_name = None
            plus_one_last_name = None
            if guest.bring_a_plus_one_id:
                plus_one_stmt = select(Guest).where(
                    Guest.uuid == guest.bring_a_plus_one_id
                )
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
                guest_uuid=guest.uuid,
                token=rsvp_info.rsvp_token,
                first_name=guest.first_name,
                last_name=guest.last_name,
                phone=guest.phone,
                status=rsvp_info.status,
                plus_one_of_id=guest.plus_one_of_id,
                family_id=family_id,
                family_members=family_members,
                plus_one_email=plus_one_email,
                plus_one_first_name=plus_one_first_name,
                plus_one_last_name=plus_one_last_name,
                attending=attending,
                dietary_requirements=dietary_requirements,
            )
