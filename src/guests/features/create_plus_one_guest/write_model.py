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
from src.guests.dtos import RSVPDTO, GuestDTO, GuestStatus, Language, PlusOneDTO
from src.guests.repository.orm_models import DietaryOption, Guest, RSVPInfo
from src.models.user import User


class CannotAddPlusOneError(Exception):
    """Raised when a plus-one guest tries to add their own plus-one."""

    pass


class CannotChangePlusOneEmailError(Exception):
    """Raised when attempting to change a plus-one's email."""

    pass


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
    def set_session_overwrite(self, session: AsyncSession) -> None:
        """
        Set the session to use for database operations.
        """
        raise NotImplementedError

    @abstractmethod
    def set_email_service(self, email_service) -> None:
        """
        Set the email service instance.
        """
        raise NotImplementedError


class SqlPlusOneGuestWriteModel(PlusOneGuestWriteModel):
    """SQL implementation of plus-one guest creation write operations."""

    async_session_manager = staticmethod(partial(async_session_manager))

    def __init__(self, session_overwrite: AsyncSession | None = None) -> None:
        self._session_overwrite = session_overwrite
        self._email_service = None

    def set_session_overwrite(self, session: AsyncSession) -> None:
        self._session_overwrite = session

    def set_email_service(self, email_service) -> None:
        self._email_service = email_service

    async def create_plus_one_guest(
        self,
        original_guest_id: UUID,
        plus_one_data: PlusOneDTO,
    ) -> tuple[GuestDTO, UUID]:
        """
        Create a new plus-one guest with user, guest, and RSVPInfo.
        Returns tuple of (GuestDTO with RSVP token and link, plus-one guest UUID).
        Raises CannotAddPlusOneError if the original guest is itself a plus-one.
        Raises CannotChangePlusOneEmailError if trying to change an existing plus-one's email.
        """
        async with self.async_session_manager(session_overwrite=self._session_overwrite) as session:
            # 1. Validate that original guest can add a plus-one
            await self._check_guest_can_add_plus_one(session, original_guest_id)

            # 2. Check if trying to change an existing plus-one's email
            # This must be done BEFORE getting/creating the user
            await self._check_plus_one_email_not_changed(
                session, original_guest_id, plus_one_data.email
            )

            # 3. Get or create User by email
            user = await self._get_or_create_user(session, str(plus_one_data.email))

            # 4. Check if user already has a guest - if so, return their info
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

            # 5. Get original guest's preferred language
            original_guest_for_lang = await session.execute(
                select(Guest).where(Guest.uuid == original_guest_id)
            )
            original_guest_obj = original_guest_for_lang.scalar_one()
            preferred_language = getattr(original_guest_obj, "preferred_language", Language.EN)

            # 6. Create Guest linked to User with plus_one_of_id set
            guest = Guest(
                user_id=user.uuid,
                first_name=plus_one_data.first_name,
                last_name=plus_one_data.last_name,
                phone=None,
                plus_one_of_id=original_guest_id,
                notes=None,
                preferred_language=preferred_language,
                allergies=plus_one_data.allergies,
            )
            session.add(guest)
            await session.flush()

            # 6a. Create DietaryOption records if provided
            if plus_one_data.dietary_requirements:
                for req in plus_one_data.dietary_requirements:
                    dietary_option = DietaryOption(
                        guest_id=guest.uuid,
                        requirement_type=req.requirement_type,
                        notes=req.notes,
                    )
                    session.add(dietary_option)
                await session.flush()

            # 7. Create RSVPInfo linked to Guest
            rsvp_token = str(uuid4())
            lang_prefix = (
                preferred_language.value
                if hasattr(preferred_language, "value")
                else preferred_language
            )
            rsvp_info = RSVPInfo(
                guest_id=guest.uuid,
                status=GuestStatus.PENDING,
                active=True,
                rsvp_token=rsvp_token,
                rsvp_link=f"{settings.frontend_url}/{lang_prefix}/rsvp/?token={rsvp_token}&plus_one=true",
                notes=None,
                email_sent_on=None,  # Default to None, plus-one gets invite via original guest
            )
            session.add(rsvp_info)

            await session.flush()

            # 7. Update the original guest's bring_a_plus_one_id
            original_guest_result = await session.execute(
                select(Guest).where(Guest.uuid == original_guest_id)
            )
            original_guest_db = original_guest_result.scalar_one()
            original_guest_db.bring_a_plus_one_id = guest.uuid
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

    async def _check_guest_can_add_plus_one(
        self, session: AsyncSession, original_guest_id: UUID
    ) -> None:
        """Check if the original guest can add a plus-one.

        A guest who is already a plus-one (has plus_one_of_id set) cannot add their own plus-one.
        """
        result = await session.execute(select(Guest).where(Guest.uuid == original_guest_id))
        guest = result.scalar_one_or_none()
        if guest is None:
            raise ValueError(f"Guest with ID {original_guest_id} not found")

        # A guest who is already a plus-one cannot add their own plus-one
        if guest.plus_one_of_id is not None:
            raise CannotAddPlusOneError("A guest who is a plus-one cannot add their own plus-one")

    async def _check_plus_one_email_not_changed(
        self, session: AsyncSession, original_guest_id: UUID, new_email: str
    ) -> None:
        """Check if trying to change an existing plus-one's email.

        If the original guest already has a plus-one with the same name but
        a different email is being provided, raise an error.
        """
        # Get the original guest's plus-one (if any)
        original_guest_result = await session.execute(
            select(Guest).where(Guest.uuid == original_guest_id)
        )
        original_guest = original_guest_result.scalar_one_or_none()
        if original_guest is None:
            return

        # Check if original guest has a plus-one
        if original_guest.bring_a_plus_one_id is None:
            return

        # Get the plus-one guest
        plus_one_result = await session.execute(
            select(Guest).where(Guest.uuid == original_guest.bring_a_plus_one_id)
        )
        plus_one_guest = plus_one_result.scalar_one_or_none()
        if plus_one_guest is None:
            return

        # Get the plus-one's user
        user_result = await session.execute(select(User).where(User.uuid == plus_one_guest.user_id))
        plus_one_user = user_result.scalar_one_or_none()

        if plus_one_user is not None and plus_one_user.email != new_email:
            raise CannotChangePlusOneEmailError("Cannot change the email of a guest's plus-one")
