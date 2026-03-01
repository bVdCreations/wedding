"""Write model for creating guests.

Creates or gets User by email, creates Guest linked to User, and creates RSVPInfo linked to Guest.
Returns DTOs instead of ORM models.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from functools import partial
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.config.settings import settings
from src.email_service.base import EmailServiceBase
from src.guests.dtos import RSVPDTO, GuestAlreadyExistsError, GuestDTO, GuestStatus, Language
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
        notes: str | None = None,
        send_email: bool = True,
        preferred_language: Language = Language.EN,
    ) -> GuestDTO:
        """Create a new guest with user and RSVP info. Returns DTO.

        Args:
            email: The guest's email address
            first_name: Optional first name
            last_name: Optional last name
            phone: Optional phone number
            notes: Optional notes
            send_email: Whether to send invitation email (default True)
            preferred_language: Preferred language for communication (default English)
        """
        raise NotImplementedError


class SqlGuestCreateWriteModel(GuestCreateWriteModel):
    """SQL implementation of guest creation write operations."""

    async_session_manager = staticmethod(partial(async_session_manager))

    def __init__(
        self,
        session_overwrite: AsyncSession | None = None,
        email_service: EmailServiceBase | None = None,
    ) -> None:
        self.session_overwrite = session_overwrite
        self.email_service = email_service
        self.seen = set()

    async def create_guest(
        self,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
        send_email: bool = True,
        preferred_language: Language = Language.EN,
    ) -> GuestDTO:
        """Create a new guest with user and RSVP info. Returns DTO.

        Args:
            email: The guest's email address
            first_name: Optional first name
            last_name: Optional last name
            phone: Optional phone number
            notes: Optional notes
            send_email: Whether to send invitation email (default True)
            preferred_language: Preferred language for communication (default English)
        """
        async with self.async_session_manager(session_overwrite=self.session_overwrite) as session:
            # 1. Get or create User by email
            user = await self._get_or_create_user(session, email)

            # 2. Check if user already has a guest
            existing_guest = await self._get_guest_by_user_id(session, user.uuid)
            if existing_guest is not None:
                raise GuestAlreadyExistsError(email)

            # 3. Create Guest linked to User
            guest = Guest(
                user_id=user.uuid,
                first_name=first_name or "",
                last_name=last_name or "",
                phone=phone,
                notes=notes,
                preferred_language=preferred_language,
            )
            session.add(guest)
            await session.flush()  # Get guest.id without full refresh

            # 4. Create RSVPInfo linked to Guest
            rsvp_token = str(uuid4())
            lang_prefix = preferred_language.value
            rsvp_info = RSVPInfo(
                guest_id=guest.uuid,
                status=GuestStatus.PENDING,
                active=True,
                rsvp_token=rsvp_token,
                rsvp_link=f"{settings.frontend_url}/{lang_prefix}/rsvp/?token={rsvp_token}",
                notes=None,
                email_sent_on=None,  # Default to None, will set timestamp if email sent
            )
            session.add(rsvp_info)

            # 5. Send invitation email if requested and email is provided
            email_sent_on = None
            if send_email and email and email.strip():
                try:
                    if self.email_service:
                        await self.email_service.send_invitation(
                            to_address=email,
                            guest_name=f"{first_name or ''} {last_name or ''}".strip() or "Guest",
                            event_date="August 15, 2026",
                            event_location="Castillo de Example, Spain",
                            rsvp_url=rsvp_info.rsvp_link,
                            response_deadline="July 15, 2026",
                            language=preferred_language,
                            guest_id=guest.uuid,
                            user_id=user.uuid,
                        )
                        email_sent_on = datetime.now(UTC)
                except Exception:
                    # Log error but don't fail guest creation
                    email_sent_on = None

            # Update email_sent_on timestamp in database
            rsvp_info.email_sent_on = email_sent_on

            await session.flush()

        # 6. Build and return GuestDTO
        return GuestDTO(
            id=guest.uuid,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            rsvp=RSVPDTO(
                status=GuestStatus(rsvp_info.status),
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

    async def _get_guest_by_user_id(self, session, user_id: UUID) -> Guest | None:
        """Check if a guest already exists for the given user ID."""
        result = await session.execute(select(Guest).where(Guest.user_id == user_id))
        return result.scalar_one_or_none()
