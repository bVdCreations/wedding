from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from src.email.service import email_service
from src.guests.dtos import (
    DietaryType,
    FamilyMemberUpdateDTO,
    GuestInfoUpdateDTO,
    GuestStatus,
    PlusOneDTO,
)
from src.guests.features.create_plus_one_guest.write_model import (
    SqlPlusOneGuestWriteModel,
)
from src.guests.repository.write_models import RSVPWriteModel, SqlRSVPWriteModel
from src.guests.urls import UPDATE_RSVP_URL

router = APIRouter()


class DietaryRequirementCreate(BaseModel):
    requirement_type: DietaryType


class PlusOneSubmit(BaseModel):
    """Submit plus one details."""

    email: EmailStr
    first_name: str
    last_name: str


class GuestInfoSubmit(BaseModel):
    """Submit guest info updates."""

    first_name: str
    last_name: str
    phone: str | None = None


class FamilyMemberSubmit(BaseModel):
    """Submit family member updates."""

    attending: bool
    dietary_requirements: list[DietaryRequirementCreate] = []
    guest_info: GuestInfoSubmit | None = None


class RSVPResponseSubmit(BaseModel):
    attending: bool
    plus_one_details: PlusOneSubmit | None = None
    dietary_requirements: list[DietaryRequirementCreate] = []
    guest_info: GuestInfoSubmit | None = None
    family_member_updates: dict[str, FamilyMemberSubmit] = {}


class RSVPResponse(BaseModel):
    message: str
    attending: bool
    status: GuestStatus


def get_rsvp_write_model() -> RSVPWriteModel:
    """Dependency to get RSVP write model instance."""
    plus_one_write_model = SqlPlusOneGuestWriteModel()
    return SqlRSVPWriteModel(
        email_service=email_service,
        plus_one_guest_write_model=plus_one_write_model,
    )


@router.post(UPDATE_RSVP_URL, response_model=RSVPResponse)
async def submit_rsvp(
    token: str,
    rsvp_data: RSVPResponseSubmit,
    write_model: RSVPWriteModel = Depends(get_rsvp_write_model),
) -> RSVPResponse:
    """
    Submit RSVP response for a guest.
    Supports updating guest info and family member RSVP/dietary.
    Family members cannot add plus-ones.
    """
    # Convert plus_one_details to DTO if provided
    plus_one_dto = None
    if rsvp_data.plus_one_details:
        plus_one_dto = PlusOneDTO(
            email=rsvp_data.plus_one_details.email,
            first_name=rsvp_data.plus_one_details.first_name,
            last_name=rsvp_data.plus_one_details.last_name,
        )

    # Convert guest_info to DTO if provided
    guest_info_dto = None
    if rsvp_data.guest_info:
        guest_info_dto = GuestInfoUpdateDTO(
            first_name=rsvp_data.guest_info.first_name,
            last_name=rsvp_data.guest_info.last_name,
            phone=rsvp_data.guest_info.phone,
        )

    # Convert family_member_updates to dict of UUID -> FamilyMemberUpdateDTO
    family_updates: dict[UUID, FamilyMemberUpdateDTO] = {}
    for member_id, update_data in rsvp_data.family_member_updates.items():
        guest_info_update = None
        if update_data.guest_info:
            guest_info_update = GuestInfoUpdateDTO(
                first_name=update_data.guest_info.first_name,
                last_name=update_data.guest_info.last_name,
                phone=update_data.guest_info.phone,
            )

        family_updates[UUID(member_id)] = FamilyMemberUpdateDTO(
            attending=update_data.attending,
            dietary_requirements=[
                {"requirement_type": req.requirement_type}
                for req in update_data.dietary_requirements
            ],
            guest_info=guest_info_update,
        )

    try:
        response_dto = await write_model.submit_rsvp(
            token=token,
            attending=rsvp_data.attending,
            plus_one_details=plus_one_dto,
            dietary_requirements=[
                {"requirement_type": req.requirement_type} for req in rsvp_data.dietary_requirements
            ],
            guest_info=guest_info_dto,
            family_member_updates=family_updates,
        )

        return RSVPResponse(
            message=response_dto.message,
            attending=response_dto.attending,
            status=response_dto.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
