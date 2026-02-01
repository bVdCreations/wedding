from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.routers.rsvp.schemas import (
    RSVPTokenResponse,
    RSVPResponseSubmit,
    RSVPResponse,
    DietaryRequirementCreate,
)
from src.routers.rsvp.service import RSVPReadService, RSVPWriteService
from src.email.service import email_service, EmailService
from src.models.guest import GuestStatus


router = APIRouter()


def get_email_service() -> EmailService:
    """Dependency to get email service instance."""
    return email_service


@router.get("/{token}", response_model=RSVPTokenResponse)
async def get_rsvp_page(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> RSVPTokenResponse:
    """
    Get RSVP page information by token.
    Returns guest and event details for rendering the RSVP form.
    """
    guest, event = await RSVPReadService.get_rsvp_info(db, token)

    if not guest:
        raise HTTPException(status_code=404, detail="Invalid or expired RSVP link")

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return RSVPTokenResponse(
        token=token,
        guest_name=guest.name,
        event_name=event.name,
        event_date=event.date.strftime("%B %d, %Y at %I:%M %p"),
        event_location=event.location or "TBA",
        status=guest.status,
        is_plus_one=guest.is_plus_one,
        plus_one_name=guest.plus_one_name,
    )


@router.post("/{token}/respond", response_model=RSVPResponse)
async def submit_rsvp(
    token: str,
    rsvp_data: RSVPResponseSubmit,
    db: AsyncSession = Depends(get_db),
    email_svc: EmailService = Depends(get_email_service),
) -> RSVPResponse:
    """
    Submit RSVP response for a guest.
    """
    try:
        write_service = RSVPWriteService(email_service=email_svc)
        guest = await write_service.submit_rsvp(
            db=db,
            token=token,
            attending=rsvp_data.attending,
            plus_one=rsvp_data.plus_one,
            plus_one_name=rsvp_data.plus_one_name,
            dietary_requirements=[
                {
                    "requirement_type": req.requirement_type,
                    "notes": req.notes,
                }
                for req in rsvp_data.dietary_requirements
            ],
        )

        message = (
            "Thank you for confirming your attendance!"
            if rsvp_data.attending
            else "We're sorry you can't make it. Your response has been recorded."
        )

        return RSVPResponse(
            message=message,
            attending=rsvp_data.attending,
            status=guest.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
