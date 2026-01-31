from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from src.models.guest import GuestStatus


class GuestCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    event_id: str
    is_plus_one: bool = False
    plus_one_name: Optional[str] = None
    notes: Optional[str] = None


class GuestUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_plus_one: Optional[bool] = None
    plus_one_name: Optional[str] = None
    notes: Optional[str] = None


class GuestResponse(BaseModel):
    id: str
    event_id: str
    name: str
    email: str
    phone: Optional[str]
    status: GuestStatus
    is_plus_one: bool
    plus_one_of_id: Optional[str]
    plus_one_name: Optional[str]
    rsvp_token: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuestListResponse(BaseModel):
    guests: List[GuestResponse]
    total: int


class InviteGuestResponse(BaseModel):
    message: str
    guest_id: str
    email: str
