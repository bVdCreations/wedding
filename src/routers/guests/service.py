import uuid

from sqlalchemy import select

from src.config.database import async_session_manager
from src.config.settings import settings
from src.email.service import email_service
from src.models.guest import Guest, GuestStatus


class GuestReadService:
    """Read-only operations for guests."""

    @staticmethod
    def generate_rsvp_token() -> str:
        return str(uuid.uuid4())

    @staticmethod
    async def get_guest(guest_id: str) -> Guest | None:
        """Get a guest by ID."""
        async with async_session_manager() as session:
            result = await session.execute(select(Guest).where(Guest.id == guest_id))
            return result.scalar_one_or_none()

    @staticmethod
    async def get_guest_by_token(token: str) -> Guest | None:
        """Get a guest by RSVP token."""
        async with async_session_manager() as session:
            result = await session.execute(select(Guest).where(Guest.rsvp_token == token))
            return result.scalar_one_or_none()

    @staticmethod
    async def get_guests(
        event_id: str | None = None,
        status: GuestStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Guest], int]:
        """Get list of guests with optional filtering."""
        async with async_session_manager() as session:
            query = select(Guest)
            count_query = select(Guest)

            if event_id:
                query = query.where(Guest.event_id == event_id)
                count_query = count_query.where(Guest.event_id == event_id)

            if status:
                query = query.where(Guest.status == status)
                count_query = count_query.where(Guest.status == status)

            # Get total count
            count_result = await session.execute(count_query)
            total = len(count_result.scalars().all())

            # Get paginated results
            query = query.offset(skip).limit(limit).order_by(Guest.created_at.desc())
            result = await session.execute(query)
            guests = result.scalars().all()

            return list(guests), total


class GuestWriteService:
    """Write operations for guests."""

    @staticmethod
    async def create_guest(
        name: str,
        email: str,
        event_id: str,
        phone: str | None = None,
        is_plus_one: bool = False,
        plus_one_name: str | None = None,
        notes: str | None = None,
    ) -> Guest:
        """Create a new guest."""
        async with async_session_manager() as session:
            guest = Guest(
                event_id=event_id,
                name=name,
                email=email,
                phone=phone,
                is_plus_one=is_plus_one,
                plus_one_name=plus_one_name,
                notes=notes,
                rsvp_token=GuestReadService.generate_rsvp_token(),
                status=GuestStatus.PENDING,
            )
            session.add(guest)
            await session.refresh(guest)
            return guest

    @staticmethod
    async def update_guest(
        guest_id: str,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        is_plus_one: bool | None = None,
        plus_one_name: str | None = None,
        notes: str | None = None,
    ) -> Guest:
        """Update a guest's information."""
        async with async_session_manager() as session:
            result = await session.execute(select(Guest).where(Guest.id == guest_id))
            guest = result.scalar_one_or_none()
            if not guest:
                raise ValueError("Guest not found")

            if name is not None:
                guest.name = name
            if email is not None:
                guest.email = email
            if phone is not None:
                guest.phone = phone
            if is_plus_one is not None:
                guest.is_plus_one = is_plus_one
            if plus_one_name is not None:
                guest.plus_one_name = plus_one_name
            if notes is not None:
                guest.notes = notes

            await session.refresh(guest)
            return guest

    @staticmethod
    async def delete_guest(guest_id: str) -> None:
        """Delete a guest."""
        async with async_session_manager() as session:
            result = await session.execute(select(Guest).where(Guest.id == guest_id))
            guest = result.scalar_one_or_none()
            if guest:
                await session.delete(guest)

    @staticmethod
    async def send_invitation(guest_id: str, event_id: str) -> None:
        """Send invitation email to a guest."""
        async with async_session_manager() as session:
            from src.models.event import Event

            # Get guest
            guest_result = await session.execute(select(Guest).where(Guest.id == guest_id))
            guest = guest_result.scalar_one_or_none()
            if not guest:
                raise ValueError("Guest not found")

            # Get event
            event_result = await session.execute(select(Event).where(Event.id == event_id))
            event = event_result.scalar_one_or_none()
            if not event:
                raise ValueError("Event not found")

        # Send email outside of session
        rsvp_url = f"{settings.frontend_url}/rsvp/{guest.rsvp_token}"

        await email_service.send_invitation(
            to_address=guest.email,
            guest_name=guest.name,
            event_date=event.date.strftime("%B %d, %Y at %I:%M %p"),
            event_location=event.location or "TBA",
            rsvp_url=rsvp_url,
            response_deadline="two weeks",
            couple_names="[Couple Names]",  # TODO: Make configurable
        )

    @staticmethod
    async def update_rsvp_response(
        guest_id: str,
        attending: bool,
        plus_one: bool,
        plus_one_name: str | None = None,
    ) -> Guest:
        """Update a guest's RSVP response."""
        async with async_session_manager() as session:
            result = await session.execute(select(Guest).where(Guest.id == guest_id))
            guest = result.scalar_one_or_none()
            if not guest:
                raise ValueError("Guest not found")

            guest.status = GuestStatus.CONFIRMED if attending else GuestStatus.DECLINED
            guest.is_plus_one = plus_one
            guest.plus_one_name = plus_one_name if attending else None

            await session.refresh(guest)
            return guest


# Keep GuestService as an alias for backward compatibility
GuestService = GuestWriteService
