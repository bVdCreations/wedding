from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.guests.dtos import DietaryType, GuestStatus
from src.guests.repository.read_models import RSVPReadModel, SqlRSVPReadModel
from src.guests.urls import GET_GUEST_INFO_URL

router = APIRouter()


class DietaryRequirementResponse(BaseModel):
    """Response for dietary requirement."""

    requirement_type: DietaryType


class RSVPTokenResponse(BaseModel):
    """Response for RSVP info - token removed as it's in the URL."""

    guest_name: str
    status: GuestStatus
    is_plus_one: bool
    plus_one_name: str | None
    dietary_requirements: list[DietaryRequirementResponse]
    attending: bool | None = None


def get_rsvp_read_model() -> RSVPReadModel:
    """Dependency to get RSVP read model instance."""
    return SqlRSVPReadModel()


@router.get(GET_GUEST_INFO_URL, response_model=RSVPTokenResponse)
async def get_guest_info(
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
        guest_name=rsvp_info.name,
        status=rsvp_info.status,
        is_plus_one=rsvp_info.is_plus_one,
        plus_one_name=rsvp_info.plus_one_name,
        attending=rsvp_info.attending,
        dietary_requirements=[
            DietaryRequirementResponse(**req) for req in rsvp_info.dietary_requirements
        ],
    )
