from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.guests.dtos import DietaryType, FamilyMemberDTO, GuestStatus
from src.guests.repository.read_models import RSVPReadModel, SqlRSVPReadModel
from src.guests.urls import GET_GUEST_INFO_URL

router = APIRouter()


class DietaryRequirementResponse(BaseModel):
    """Response for dietary requirement."""

    requirement_type: DietaryType


class PlusOneResponse(BaseModel):
    """Response for plus-one guest details."""

    email: str
    first_name: str
    last_name: str


class FamilyMemberResponse(BaseModel):
    """Response for family member details."""

    uuid: UUID
    first_name: str
    last_name: str
    attending: bool | None = None
    dietary_requirements: list[DietaryRequirementResponse]
    phone: str | None = None


class RSVPTokenResponse(BaseModel):
    """Response for RSVP info - token removed as it's in the URL."""

    guest_uuid: UUID
    first_name: str
    last_name: str
    phone: str | None = None
    status: GuestStatus
    is_plus_one: bool  # Derived from plus_one_of_id presence
    is_family_member: bool  # Derived from family_id presence
    family_id: UUID | None = None
    family_members: list[FamilyMemberResponse] = []
    plus_one: PlusOneResponse | None = None
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
    Includes family members if guest is part of a family.
    """
    rsvp_info = await read_model.get_rsvp_info(token)

    if not rsvp_info:
        raise HTTPException(status_code=404, detail="Invalid or expired RSVP link")

    # Build nested plus_one object if guest has a plus-one
    plus_one = None
    if rsvp_info.plus_one_email and rsvp_info.plus_one_first_name and rsvp_info.plus_one_last_name:
        plus_one = PlusOneResponse(
            email=rsvp_info.plus_one_email,
            first_name=rsvp_info.plus_one_first_name,
            last_name=rsvp_info.plus_one_last_name,
        )

    # Build family members response
    family_members = []
    for member in rsvp_info.family_members:
        family_members.append(
            FamilyMemberResponse(
                uuid=member.uuid,
                first_name=member.first_name,
                last_name=member.last_name,
                attending=member.attending,
                phone=member.phone,
                dietary_requirements=[
                    DietaryRequirementResponse(**req)
                    for req in member.dietary_requirements
                ],
            )
        )

    return RSVPTokenResponse(
        guest_uuid=rsvp_info.guest_uuid,
        first_name=rsvp_info.first_name,
        last_name=rsvp_info.last_name,
        phone=rsvp_info.phone,
        status=rsvp_info.status,
        is_plus_one=rsvp_info.plus_one_of_id is not None,
        is_family_member=rsvp_info.family_id is not None,
        family_id=rsvp_info.family_id,
        family_members=family_members,
        plus_one=plus_one,
        attending=rsvp_info.attending,
        dietary_requirements=[
            DietaryRequirementResponse(**req) for req in rsvp_info.dietary_requirements
        ],
    )
