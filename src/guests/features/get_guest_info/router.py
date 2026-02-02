from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.email.service import EmailService, email_service
from src.guests.dtos import GuestStatus
from src.guests.repository.read_models import RSVPReadModel, SqlRSVPReadModel

router = APIRouter()


class RSVPTokenResponse(BaseModel):
    token: str
    guest_name: str
    event_name: str
    event_date: str
    event_location: str
    status: GuestStatus
    is_plus_one: bool
    plus_one_name: str | None


def get_email_service() -> EmailService:
    """Dependency to get email service instance."""
    return email_service


def get_rsvp_read_model() -> RSVPReadModel:
    """Dependency to get RSVP read model instance."""
    return SqlRSVPReadModel()


@router.get("/{token}", response_model=RSVPTokenResponse)
async def get_rsvp_page(
    token: str,
    read_model: RSVPReadModel = Depends(get_rsvp_read_model),
) -> RSVPTokenResponse:
    """
    Get RSVP page information by token.
    Returns guest and event details for rendering the RSVP form.
    """
    rsvp_info = await read_model.get_rsvp_info(token)

    if not rsvp_info:
        raise HTTPException(status_code=404, detail="Invalid or expired RSVP link")

    return RSVPTokenResponse(
        token=rsvp_info.token,
        guest_name=rsvp_info.name,
        event_name=rsvp_info.event_name,
        event_date=rsvp_info.event_date,
        event_location=rsvp_info.event_location,
        status=rsvp_info.status,
        is_plus_one=rsvp_info.is_plus_one,
        plus_one_name=rsvp_info.plus_one_name,
    )
