from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.email.service import EmailService, email_service
from src.routers.rsvp.models import RSVPReadModel, RSVPWriteModel
from src.routers.rsvp.schemas import (
    RSVPResponse,
    RSVPResponseSubmit,
    RSVPTokenResponse,
)

router = APIRouter()


def get_email_service() -> EmailService:
    """Dependency to get email service instance."""
    return email_service


def get_rsvp_read_model() -> RSVPReadModel:
    """Dependency to get RSVP read model instance."""
    return RSVPReadModel()


def get_rsvp_write_model(
    email_svc: EmailService = Depends(get_email_service),
) -> RSVPWriteModel:
    """Dependency to get RSVP write model instance."""
    return RSVPWriteModel(email_service=email_svc)


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


@router.post("/{token}/respond", response_model=RSVPResponse)
async def submit_rsvp(
    token: str,
    rsvp_data: RSVPResponseSubmit,
    write_model: RSVPWriteModel = Depends(get_rsvp_write_model),
) -> RSVPResponse:
    """
    Submit RSVP response for a guest.
    """
    try:
        response_dto = await write_model.submit_rsvp(
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

        return RSVPResponse(
            message=response_dto.message,
            attending=response_dto.attending,
            status=response_dto.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
