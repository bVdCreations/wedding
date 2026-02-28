from dataclasses import field

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator, model_validator

from src.email_service import get_email_service
from src.guests.dtos import DietaryType, GuestStatus
from src.guests.features.create_plus_one_guest.write_model import (
    SqlPlusOneGuestWriteModel,
)
from src.guests.repository.write_models import RSVPWriteModel, SqlRSVPWriteModel
from src.guests.urls import UPDATE_RSVP_URL

router = APIRouter()


class DietaryRequirement(BaseModel):
    requirement_type: DietaryType
    notes: str | None = None

    @model_validator(mode='after')
    def notes_required_for_other(self) -> 'DietaryRequirement':
        if self.requirement_type == DietaryType.OTHER and not (self.notes or '').strip():
            raise ValueError('notes are required when dietary type is "other"')
        return self


class PlusOneSubmit(BaseModel):
    """Submit plus one details."""

    email: EmailStr
    first_name: str
    last_name: str
    allergies: str | None = None
    dietary_requirements: list[DietaryRequirement] = field(default_factory=list)

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('must not be empty')
        return v.strip()


class GuestInfoSubmit(BaseModel):
    """Submit guest info updates."""

    first_name: str
    last_name: str
    phone: str | None = None
    allergies: str | None = None
    dietary_requirements: list[DietaryRequirement] = field(default_factory=list)

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('must not be empty')
        return v.strip()


class FamilyMemberSubmit(BaseModel):
    """Submit family member updates."""

    attending: bool
    guest_info: GuestInfoSubmit


class RSVPResponseSubmit(BaseModel):
    attending: bool
    plus_one_details: PlusOneSubmit | None = None
    guest_info: GuestInfoSubmit | None = None
    family_member_updates: dict[str, FamilyMemberSubmit] = {}

    @model_validator(mode='after')
    def clear_plus_one_when_not_attending(self) -> 'RSVPResponseSubmit':
        if not self.attending:
            self.plus_one_details = None
        return self


class RSVPResponse(BaseModel):
    message: str
    attending: bool
    status: GuestStatus


def get_rsvp_write_model() -> RSVPWriteModel:
    """Dependency to get RSVP write model instance."""
    plus_one_write_model = SqlPlusOneGuestWriteModel()
    return SqlRSVPWriteModel(
        email_service=get_email_service(),
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
    try:
        response_dto = await write_model.submit_rsvp(
            token=token,
            rsvp_data=rsvp_data,
        )

        return RSVPResponse(
            message=response_dto.message,
            attending=response_dto.attending,
            status=response_dto.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
