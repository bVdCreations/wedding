import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.guest import Guest, GuestStatus
from src.models.dietary import DietaryOption
from src.models.event import Event
from src.email.service import email_service
from src.config.settings import settings


class GuestService:
    @staticmethod
    def generate_rsvp_token() -> str:
        return str(uuid.uuid4())

    @staticmethod
    async def create_guest(
        db: AsyncSession,
        name: str,
        email: str,
        event_id: str,
        phone: Optional[str] = None,
        is_plus_one: bool = False,
        plus_one_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Guest:
        guest = Guest(
            event_id=event_id,
            name=name,
            email=email,
            phone=phone,
            is_plus_one=is_plus_one,
            plus_one_name=plus_one_name,
            notes=notes,
            rsvp_token=GuestService.generate_rsvp_token(),
            status=GuestStatus.PENDING,
        )
        db.add(guest)
        await db.commit()
        await db.refresh(guest)
        return guest

    @staticmethod
    async def get_guest(db: AsyncSession, guest_id: str) -> Optional[Guest]:
        result = await db.execute(select(Guest).where(Guest.id == guest_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_guest_by_token(db: AsyncSession, token: str) -> Optional[Guest]:
        result = await db.execute(select(Guest).where(Guest.rsvp_token == token))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_guests(
        db: AsyncSession,
        event_id: Optional[str] = None,
        status: Optional[GuestStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Guest], int]:
        query = select(Guest)
        count_query = select(Guest)

        if event_id:
            query = query.where(Guest.event_id == event_id)
            count_query = count_query.where(Guest.event_id == event_id)

        if status:
            query = query.where(Guest.status == status)
            count_query = count_query.where(Guest.status == status)

        # Get total count
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Guest.created_at.desc())
        result = await db.execute(query)
        guests = result.scalars().all()

        return list(guests), total

    @staticmethod
    async def update_guest(
        db: AsyncSession,
        guest: Guest,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        is_plus_one: Optional[bool] = None,
        plus_one_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Guest:
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

        await db.commit()
        await db.refresh(guest)
        return guest

    @staticmethod
    async def delete_guest(db: AsyncSession, guest: Guest) -> None:
        await db.delete(guest)
        await db.commit()

    @staticmethod
    async def send_invitation(
        db: AsyncSession,
        guest: Guest,
        event: Event,
    ) -> None:
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
        db: AsyncSession,
        guest: Guest,
        attending: bool,
        plus_one: bool,
        plus_one_name: Optional[str] = None,
    ) -> Guest:
        guest.status = GuestStatus.CONIRMED if attending else GuestStatus.DECLINED
        guest.is_plus_one = plus_one
        guest.plus_one_name = plus_one_name if attending else None

        await db.commit()
        await db.refresh(guest)
        return guest
