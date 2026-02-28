from fastapi import APIRouter, Depends

from src.email_service import get_email_service
from src.guests.features.request_invitation.dtos import (
    RequestInvitationRequest,
    RequestInvitationResponse,
)
from src.guests.features.request_invitation.write_model import (
    RequestInvitationWriteModel,
    SqlRequestInvitationWriteModel,
)

router = APIRouter()

REQUEST_INVITATION_URL = "/api/v1/guests/request-invitation"


def get_request_invitation_write_model() -> RequestInvitationWriteModel:
    """Dependency to get request invitation write model instance."""
    return SqlRequestInvitationWriteModel(
        email_service=get_email_service(),
    )


@router.post(
    REQUEST_INVITATION_URL,
    response_model=RequestInvitationResponse,
)
async def request_invitation(
    request: RequestInvitationRequest,
    write_model: RequestInvitationWriteModel = Depends(get_request_invitation_write_model),
) -> RequestInvitationResponse:
    """
    Request or resend an RSVP invitation.

    For new guests: creates user, guest, RSVPInfo and sends invitation email.
    For existing guests: resends invitation email.

    All fields are required: email, first_name, last_name.
    Optional: language (defaults to English).
    """
    return await write_model.request_invitation(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        language=request.language,
    )