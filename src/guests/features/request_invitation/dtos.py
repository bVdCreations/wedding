"""DTOs for request invitation feature."""

from pydantic import BaseModel, EmailStr

from src.guests.dtos import Language


class RequestInvitationRequest(BaseModel):
    """Request body for requesting an invitation."""

    email: EmailStr
    first_name: str
    last_name: str
    language: Language | None = None


class RequestInvitationResponse(BaseModel):
    """Response for invitation request."""

    message: str
