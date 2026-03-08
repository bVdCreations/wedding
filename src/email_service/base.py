from abc import ABC, abstractmethod
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.email_service.dtos import EmailResult, EmailStatus
from src.guests.dtos import Language
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User


class EmailServiceBase(ABC):
    _session_overwrite: AsyncSession | None = None

    @abstractmethod
    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        rsvp_url: str,
        guest_id: UUID,
        language: Language = Language.EN,
        user_id: UUID | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
        language: Language = Language.EN,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def send_invite_one_plus_one(
        self,
        to_address: str,
        guest_name: str,
        inviter_name: str,
        rsvp_url: str,
        language: Language = Language.EN,
        guest_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        pass

    def set_session_overwrite(self, session: AsyncSession) -> None:
        self._session_overwrite = session

    async def send_invitation_for_guest(
        self,
        guest_id: UUID | None,
    ) -> EmailResult:
        """Send invitation email for a guest and update RSVPInfo.email_sent_on."""
        if guest_id is None:
            return EmailResult(status=EmailStatus.FAILED, error="guest_id is None")
        async with async_session_manager(
            session_overwrite=self._session_overwrite
        ) as email_session:
            try:
                rsvp_info = await email_session.execute(
                    select(RSVPInfo).where(RSVPInfo.guest_id == guest_id)
                )
                rsvp_info = rsvp_info.scalar_one_or_none()
                guest = await email_session.execute(select(Guest).where(Guest.uuid == guest_id))
                guest = guest.scalar_one_or_none()
                if not guest:
                    raise Exception("Guest not found")
                if not rsvp_info:
                    raise Exception("RSVPInfo not found")
                if not guest.user_id:
                    raise Exception("User not found")
                user = await email_session.execute(select(User).where(User.uuid == guest.user_id))
                user = user.scalar_one_or_none()
                if not user:
                    raise Exception("User not found")
                rsvp_info.email_sent_on = datetime.now(UTC)
                await email_session.flush()
                guest_name = f"{guest.first_name} {guest.last_name}".strip() or "Guest"
                rsvp_url = rsvp_info.rsvp_link
                email_address = user.email
                language = (
                    Language(guest.preferred_language) if guest.preferred_language else Language.EN
                )
                await self.send_invitation(
                    to_address=email_address,
                    guest_name=guest_name,
                    rsvp_url=rsvp_url,
                    guest_id=guest_id,
                    language=language,
                )
            except Exception as e:
                await email_session.rollback()
                return EmailResult(status=EmailStatus.FAILED, error=str(e))
            else:
                await email_session.commit()
                return EmailResult(status=EmailStatus.SENT)
