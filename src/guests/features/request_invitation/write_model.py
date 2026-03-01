"""Write model for request invitation feature.

Handles both new guest creation and resending invitation to existing guests.
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
from src.guests.dtos import Language
from src.guests.features.request_invitation.dtos import RequestInvitationResponse
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User


class RequestInvitationWriteModel(ABC):
    """Abstract base class for request invitation write operations."""

    @abstractmethod
    async def request_invitation(
        self,
        email: str,
        first_name: str,
        last_name: str,
        language: Language | None = None,
    ) -> RequestInvitationResponse:
        """Request or resend an invitation email.

        Args:
            email: The guest's email address
            first_name: The guest's first name (used for new guests)
            last_name: The guest's last name (used for new guests)
            language: Preferred language (defaults to English if not provided)

        Returns:
            RequestInvitationResponse with success message
        """
        raise NotImplementedError


class SqlRequestInvitationWriteModel(RequestInvitationWriteModel):
    """SQL implementation of request invitation write operations."""

    async_session_manager = staticmethod(partial(async_session_manager))

    def __init__(
        self,
        session_overwrite: AsyncSession | None = None,
        email_service: EmailServiceBase | None = None,
    ) -> None:
        self.session_overwrite = session_overwrite
        self.email_service = email_service
        self.seen = set()

    async def request_invitation(
        self,
        email: str,
        first_name: str,
        last_name: str,
        language: Language | None = None,
    ) -> RequestInvitationResponse:
        """Request or resend an invitation email.

        Args:
            email: The guest's email address
            first_name: The guest's first name (used for new guests)
            last_name: The guest's last name (used for new guests)
            language: Preferred language (defaults to English if not provided)

        Returns:
            RequestInvitationResponse with success message
        """
        # Default to English if no language provided
        preferred_language = language or Language.EN

        async with self.async_session_manager(session_overwrite=self.session_overwrite) as session:
            # 1. Check if User exists
            user = await self._get_user_by_email(session, email)

            if user is not None:
                # 2. Check if user has a guest
                guest = await self._get_guest_by_user_id(session, user.uuid)
                if guest is not None:
                    # Guest exists - resend invitation (update preferred language if provided)
                    if language:
                        guest.preferred_language = language
                        await session.flush()
                    await self._resend_invitation(session, user, guest)
                    return RequestInvitationResponse(
                        message="Check your email for your invitation link"
                    )

            # 3. No guest exists - create new guest
            # Get or create user (should exist now after check above, but handle race)
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

            # Create Guest
            guest = Guest(
                user_id=user.uuid,
                first_name=first_name,
                last_name=last_name,
                phone=None,
                notes=None,
                preferred_language=preferred_language,
            )
            session.add(guest)
            await session.flush()

            # Create RSVPInfo
            rsvp_token = str(uuid4())
            rsvp_info = RSVPInfo(
                guest_id=guest.uuid,
                status="pending",
                active=True,
                rsvp_token=rsvp_token,
                rsvp_link=f"{settings.frontend_url}/{preferred_language.value}/rsvp/?token={rsvp_token}",
                notes=None,
                email_sent_on=None,
            )
            session.add(rsvp_info)
            await session.flush()

            # Send invitation email
            email_sent_on = None
            if email and email.strip():
                try:
                    if self.email_service:
                        await self.email_service.send_invitation(
                            to_address=email,
                            guest_name=f"{first_name} {last_name}".strip(),
                            event_date="November 7, 2026",
                            event_location="Rancho del Inglés, Malaga, Spain",
                            rsvp_url=rsvp_info.rsvp_link,
                            response_deadline="September 7, 2026",
                            language=preferred_language,
                            guest_id=guest.uuid,
                            user_id=user.uuid,
                        )
                        email_sent_on = datetime.now(UTC)
                except Exception:
                    email_sent_on = None

            rsvp_info.email_sent_on = email_sent_on
            await session.flush()

        return RequestInvitationResponse(
            message="Check your email for your invitation link"
        )

    async def _get_user_by_email(self, session, email: str) -> User | None:
        """Get user by email."""
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_guest_by_user_id(self, session, user_id: UUID) -> Guest | None:
        """Check if a guest already exists for the given user ID."""
        result = await session.execute(select(Guest).where(Guest.user_id == user_id))
        return result.scalar_one_or_none()

    async def _resend_invitation(self, session, user: User, guest: Guest) -> None:
        """Resend invitation email to existing guest."""
        # Get RSVPInfo for this guest
        result = await session.execute(
            select(RSVPInfo).where(RSVPInfo.guest_id == guest.uuid)
        )
        rsvp_info = result.scalar_one_or_none()

        if not rsvp_info:
            return

        # Send invitation email
        if user.email and user.email.strip():
            try:
                if self.email_service:
                    await self.email_service.send_invitation(
                        to_address=user.email,
                        guest_name=f"{guest.first_name} {guest.last_name}".strip() or "Guest",
                        event_date="November 7, 2026",
                        event_location="Rancho del Inglés, Malaga, Spain",
                        rsvp_url=rsvp_info.rsvp_link,
                        response_deadline="September 7, 2026",
                        language=getattr(guest, "preferred_language", Language.EN),
                        guest_id=guest.uuid,
                        user_id=user.uuid,
                    )
                    rsvp_info.email_sent_on = datetime.now(UTC)
                    await session.flush()
            except Exception:
                pass
