"""Write model for creating guests.

Creates or gets User by email, creates Guest linked to User, and creates RSVPInfo linked to Guest.
Returns DTOs instead of ORM models.
"""

from abc import ABC, abstractmethod
from functools import partial
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.config.settings import settings
from src.guests.dtos import RSVPDTO, GuestDTO, GuestStatus
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User


class GuestCreateWriteModel(ABC):
    """Abstract base class for guest creation write operations."""

    @abstractmethod
    async def create_guest(
        self,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        is_plus_one: bool = False,
        plus_one_name: str | None = None,
        notes: str | None = None,
    ) -> GuestDTO:
        """Create a new guest with user and RSVP info. Returns DTO."""
        raise NotImplementedError


class SqlGuestCreateWriteModel(GuestCreateWriteModel):
    """SQL implementation of guest creation write operations."""

    async_session_manager = staticmethod(partial(async_session_manager))

    def __init__(self, session_overwrite: AsyncSession | None = None) -> None:
        self.session_overwrite = session_overwrite
        self.seen = set()

    async def create_guest(
        self,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        is_plus_one: bool = False,
        plus_one_name: str | None = None,
        notes: str | None = None,
    ) -> GuestDTO:
        """Create a new guest with user and RSVP info. Returns DTO."""
        async with self.async_session_manager(session_overwrite=self.session_overwrite) as session:
            # 1. Get or create User by email
            user = await self._get_or_create_user(session, email)

            # 2. Create Guest linked to User
            guest = Guest(
                user_id=user.uuid,
                first_name=first_name or "",
                last_name=last_name or "",
                phone=phone,
                is_plus_one=is_plus_one,
                plus_one_name=plus_one_name if is_plus_one else None,
                notes=notes,
            )
            session.add(guest)
            await session.flush()  # Get guest.id without full refresh

            # 3. Create RSVPInfo linked to Guest
            rsvp_token = str(uuid4())
            rsvp_info = RSVPInfo(
                guest_id=guest.uuid,
                status=GuestStatus.PENDING,
                active=True,
                rsvp_token=rsvp_token,
                rsvp_link=f"{settings.frontend_url}/rsvp/?token={rsvp_token}",
                notes=None,
            )
            session.add(rsvp_info)

            await session.commit()

        # 4. Build and return GuestDTO
        return GuestDTO(
            id=guest.uuid,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_plus_one=is_plus_one,
            plus_one_name=plus_one_name if is_plus_one else None,
            email=email,
            rsvp=RSVPDTO(
                status=rsvp_info.status,
                token=rsvp_token,
                link=rsvp_info.rsvp_link,
            ),
        )

    async def _get_or_create_user(self, session, email: str) -> User:
        """Get existing user by email or create a new one."""
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                uuid=uuid4(),
                email=email,
                hashed_password=None,  # No password for guest users
                is_active=True,
                is_superuser=False,
            )
            session.add(user)
            await session.flush()  # Get user.id
            # No need to commit here - it will be committed in the main transaction

        return user
