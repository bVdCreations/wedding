"""Write model for creating plus-one guests.

Creates or gets User by email, creates Guest linked to User, creates RSVPInfo with token/link.
Returns DTOs instead of ORM models.
"""

from abc import ABC, abstractmethod
from functools import partial
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.config.settings import settings
from src.guests.dtos import RSVPDTO, GuestDTO, GuestStatus, PlusOneDTO
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User


class PlusOneGuestWriteModel(ABC):
    """Abstract base class for plus-one guest creation write operations."""

    @abstractmethod
    async def create_plus_one_guest(
        self,
        original_guest_id: UUID,
        plus_one_data: PlusOneDTO,
    ) -> tuple[GuestDTO, UUID]:
        """
        Create a new plus-one guest with user, guest, and RSVPInfo.
        Returns tuple of (GuestDTO with RSVP token and link, plus-one guest UUID).
        """
        raise NotImplementedError

    @abstractmethod
    def session_overwrite(self, session: AsyncSession) -> AsyncSession:
        """
        Overwrite the session with a new session.
        """
        raise NotImplementedError


class SqlPlusOneGuestWriteModel(PlusOneGuestWriteModel):
    """SQL implementation of plus-one guest creation write operations."""

    async_session_manager = staticmethod(partial(async_session_manager))

    def __init__(self, session_overwrite: AsyncSession | None = None) -> None:
        self.session_overwrite = session_overwrite

    def session_overwrite(self, session: AsyncSession) -> AsyncSession:
        self.session_overwrite = session
        return session

    async def create_plus_one_guest(
        self,
        original_guest_id: UUID,
        plus_one_data: PlusOneDTO,
    ) -> tuple[GuestDTO, UUID]:
        """
        Create a new plus-one guest with user, guest, and RSVPInfo.
        Returns tuple of (GuestDTO with RSVP token and link, plus-one guest UUID).
        """
        async with self.async_session_manager(session_overwrite=self.session_overwrite) as session:
            # 1. Get or create User by email
            user = await self._get_or_create_user(session, str(plus_one_data.email))

            # 2. Check if user already has a guest - if so, just return their info
            existing_guest = await self._get_guest_by_user_id(session, user.uuid)
            if existing_guest is not None:
                # Return existing guest's info
                rsvp_info = await self._get_rsvp_info_by_guest_id(session, existing_guest.uuid)
                return (
                    GuestDTO(
                        id=existing_guest.uuid,
                        first_name=existing_guest.first_name,
                        last_name=existing_guest.last_name,
                        phone=existing_guest.phone,
                        plus_one_of_id=existing_guest.plus_one_of_id,
                        email=str(plus_one_data.email),
                        rsvp=RSVPDTO(
                            status=rsvp_info.status if rsvp_info else GuestStatus.PENDING,
                            token=rsvp_info.rsvp_token if rsvp_info else "",
                            link=rsvp_info.rsvp_link if rsvp_info else "",
                        ),
                    ),
                    existing_guest.uuid,
                )

            # 3. Create Guest linked to User with plus_one_of_id set
            guest = Guest(
                user_id=user.uuid,
                first_name=plus_one_data.first_name,
                last_name=plus_one_data.last_name,
                phone=None,
                plus_one_of_id=original_guest_id,
                notes=None,
            )
            session.add(guest)
            await session.flush()

            # 4. Create RSVPInfo linked to Guest
            rsvp_token = str(uuid4())
            rsvp_info = RSVPInfo(
                guest_id=guest.uuid,
                status=GuestStatus.PENDING,
                active=True,
                rsvp_token=rsvp_token,
                rsvp_link=f"{settings.frontend_url}/rsvp/?token={rsvp_token}?plus_one=true",
                notes=None,
            )
            session.add(rsvp_info)

            await session.flush()

        # 5. Build and return GuestDTO with plus-one guest UUID
        return (
            GuestDTO(
                id=guest.uuid,
                first_name=plus_one_data.first_name,
                last_name=plus_one_data.last_name,
                phone=None,
                plus_one_of_id=original_guest_id,
                email=str(plus_one_data.email),
                rsvp=RSVPDTO(
                    status=rsvp_info.status,
                    token=rsvp_token,
                    link=rsvp_info.rsvp_link,
                ),
            ),
            guest.uuid,
        )

    async def _get_or_create_user(self, session: AsyncSession, email: str) -> User:
        """Get existing user by email or create a new one."""
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                uuid=uuid4(),
                email=email,
                hashed_password=None,
                is_active=True,
                is_superuser=False,
            )
            session.add(user)
            await session.flush()

        return user

    async def _get_guest_by_user_id(self, session: AsyncSession, user_id: UUID) -> Guest | None:
        """Check if a guest already exists for the given user ID."""
        result = await session.execute(select(Guest).where(Guest.user_id == user_id))
        return result.scalar_one_or_none()

    async def _get_rsvp_info_by_guest_id(
        self, session: AsyncSession, guest_id: UUID
    ) -> RSVPInfo | None:
        """Get RSVPInfo for a guest."""
        result = await session.execute(select(RSVPInfo).where(RSVPInfo.guest_id == guest_id))
        return result.scalar_one_or_none()
