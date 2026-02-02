from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.email.service import EmailService, email_service
from src.guests.dtos import DietaryType, GuestStatus
from src.guests.repository.write_models import RSVPWriteModel, SqlRSVPWriteModel
from src.guests.urls import UPDATE_RSVP_URL

router = APIRouter()


class DietaryRequirementCreate(BaseModel):
    requirement_type: DietaryType
    notes: str | None = None


class RSVPResponseSubmit(BaseModel):
    attending: bool
    plus_one: bool = False
    plus_one_name: str | None = None
    dietary_requirements: list[DietaryRequirementCreate] = []


class RSVPResponse(BaseModel):
    message: str
    attending: bool
    status: GuestStatus


def get_email_service() -> EmailService:
    """Dependency to get email service instance."""
    return email_service


def get_rsvp_write_model(
    email_svc: EmailService = Depends(get_email_service),
) -> RSVPWriteModel:
    """Dependency to get RSVP write model instance."""
    return SqlRSVPWriteModel(email_service=email_svc)


@router.post(UPDATE_RSVP_URL, response_model=RSVPResponse)
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
