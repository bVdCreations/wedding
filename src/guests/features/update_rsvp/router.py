from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from src.email.service import EmailService, email_service
from src.guests.dtos import DietaryType, GuestStatus, PlusOneDTO
from src.guests.features.create_plus_one_guest.write_model import (
    PlusOneGuestWriteModel,
    SqlPlusOneGuestWriteModel,
)
from src.guests.repository.write_models import RSVPWriteModel, SqlRSVPWriteModel
from src.guests.urls import UPDATE_RSVP_URL

router = APIRouter()


class DietaryRequirementCreate(BaseModel):
    requirement_type: DietaryType
    notes: str | None = None


class PlusOneSubmit(BaseModel):
    """Submit plus one details."""

    email: EmailStr
    first_name: str
    last_name: str


class RSVPResponseSubmit(BaseModel):
    attending: bool
    plus_one_details: PlusOneSubmit | None = None
    dietary_requirements: list[DietaryRequirementCreate] = []


class RSVPResponse(BaseModel):
    message: str
    attending: bool
    status: GuestStatus


def get_email_service() -> EmailService:
    """Dependency to get email service instance."""
    return email_service


def get_plus_one_guest_write_model() -> PlusOneGuestWriteModel:
    """Dependency to get plus-one guest write model instance."""
    return SqlPlusOneGuestWriteModel()


def get_rsvp_write_model(
    email_svc: EmailService = Depends(get_email_service),
    plus_one_write_model: PlusOneGuestWriteModel = Depends(get_plus_one_guest_write_model),
) -> RSVPWriteModel:
    """Dependency to get RSVP write model instance."""
    return SqlRSVPWriteModel(
        email_service=email_svc,
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
    """
    # Convert plus_one_details to DTO if provided
    plus_one_dto = None
    if rsvp_data.plus_one_details:
        plus_one_dto = PlusOneDTO(
            email=rsvp_data.plus_one_details.email,
            first_name=rsvp_data.plus_one_details.first_name,
            last_name=rsvp_data.plus_one_details.last_name,
        )

    try:
        response_dto = await write_model.submit_rsvp(
            token=token,
            attending=rsvp_data.attending,
            plus_one_details=plus_one_dto,
            dietary_requirements=[
                {
                    "requirement_type": req.requirement_type,
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
