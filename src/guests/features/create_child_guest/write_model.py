"""Write model for creating child guests.

Creates a Guest with guest_type=CHILD (no User), linked to a family.
Creates RSVPInfo with empty rsvp_token and rsvp_link (no separate invite).
"""

from abc import ABC, abstractmethod
from functools import partial
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.guests.dtos import GuestDTO, GuestStatus, GuestType, RSVPDTO
from src.guests.repository.orm_models import Guest, RSVPInfo


class ChildGuestCreateWriteModel(ABC):
    """Abstract base class for child guest creation write operations."""

    @abstractmethod
    async def create_child_guest(
        self,
        family_id: UUID,
        first_name: str,
        last_name: str,
        phone: str | None = None,
    ) -> GuestDTO:
        """Create a new child guest with RSVP info. Returns DTO."""
        raise NotImplementedError


class SqlChildGuestCreateWriteModel(ChildGuestCreateWriteModel):
    """SQL implementation of child guest creation write operations."""

    async_session_manager = staticmethod(partial(async_session_manager))

    def __init__(self, session_overwrite: AsyncSession | None = None) -> None:
        self.session_overwrite = session_overwrite

    async def create_child_guest(
        self,
        family_id: UUID,
        first_name: str,
        last_name: str,
        phone: str | None = None,
    ) -> GuestDTO:
        """Create a new child guest with RSVP info. Returns DTO."""
        async with self.async_session_manager(session_overwrite=self.session_overwrite) as session:
            # Validate family exists
            from src.guests.repository.orm_models import Family
            stmt = select(Family).where(Family.uuid == family_id)
            result = await session.execute(stmt)
            family = result.scalar_one_or_none()
            if family is None:
                raise ValueError(f"Family not found: {family_id}")

            # Create Guest with guest_type=CHILD, no user_id
            guest = Guest(
                user_id=None,  # Children don't have a User
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                guest_type=GuestType.CHILD,
                family_id=family_id,
            )
            session.add(guest)
            await session.flush()  # Get guest.uuid

            # Create RSVPInfo with empty token and link (no separate invite)
            rsvp_info = RSVPInfo(
                guest_id=guest.uuid,
                status=GuestStatus.PENDING,
                active=True,
                rsvp_token="",  # Empty - no separate invite
                rsvp_link="",   # Empty - no separate invite
            )
            session.add(rsvp_info)
            await session.flush()

        # Build and return GuestDTO
        return GuestDTO(
            id=guest.uuid,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email="",  # Children don't have email
            rsvp=RSVPDTO(
                status=rsvp_info.status,
                token=rsvp_info.rsvp_token,
                link=rsvp_info.rsvp_link,
            ),
            family_id=family_id,
        )
