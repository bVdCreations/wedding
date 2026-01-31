from typing import Optional, List
from pydantic import BaseModel
from src.models.guest import GuestStatus
from src.models.dietary import DietaryType


class RSVPTokenResponse(BaseModel):
    token: str
    guest_name: str
    event_name: str
    event_date: str
    event_location: str
    status: GuestStatus
    is_plus_one: bool
    plus_one_name: Optional[str]


class DietaryRequirementCreate(BaseModel):
    requirement_type: DietaryType
    notes: Optional[str] = None


class RSVPResponseSubmit(BaseModel):
    attending: bool
    plus_one: bool = False
    plus_one_name: Optional[str] = None
    dietary_requirements: List[DietaryRequirementCreate] = []


class RSVPResponse(BaseModel):
    message: str
    attending: bool
    status: GuestStatus
