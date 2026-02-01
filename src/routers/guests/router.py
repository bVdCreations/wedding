from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from src.routers.guests.schemas import (
    GuestCreate,
    GuestListResponse,
    GuestResponse,
    GuestUpdate,
    InviteGuestResponse,
)
from src.routers.guests.service import GuestReadService, GuestWriteService

router = APIRouter()


@router.get("/", response_model=GuestListResponse)
async def list_guests(
    event_id: str | None = Query(None, description="Filter by event ID"),
    status: str | None = Query(None, description="Filter by RSVP status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> GuestListResponse:
    """
    List all guests with optional filtering by event and status.
    """
    from src.models.guest import GuestStatus

    status_enum = GuestStatus(status) if status else None
    guests, total = await GuestReadService.get_guests(
        event_id=event_id, status=status_enum, skip=skip, limit=limit
    )
    return GuestListResponse(
        guests=[GuestResponse.model_validate(g) for g in guests],
        total=total,
    )


@router.post("/", response_model=GuestResponse, status_code=201)
async def create_guest(
    guest_data: GuestCreate,
) -> GuestResponse:
    """
    Create a new guest.
    """

    guest = await GuestWriteService.create_guest(
        name=guest_data.name,
        email=guest_data.email,
        event_id=guest_data.event_id,
        phone=guest_data.phone,
        is_plus_one=guest_data.is_plus_one,
        plus_one_name=guest_data.plus_one_name,
        notes=guest_data.notes,
    )
    return GuestResponse.model_validate(guest)


@router.get("/{guest_id}", response_model=GuestResponse)
async def get_guest(
    guest_id: str,
) -> GuestResponse:
    """
    Get a specific guest by ID.
    """
    guest = await GuestReadService.get_guest(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return GuestResponse.model_validate(guest)


@router.put("/{guest_id}", response_model=GuestResponse)
async def update_guest(
    guest_id: str,
    guest_data: GuestUpdate,
) -> GuestResponse:
    """
    Update a guest's information.
    """
    guest = await GuestWriteService.update_guest(
        guest_id=guest_id,
        name=guest_data.name,
        email=guest_data.email,
        phone=guest_data.phone,
        is_plus_one=guest_data.is_plus_one,
        plus_one_name=guest_data.plus_one_name,
        notes=guest_data.notes,
    )
    return GuestResponse.model_validate(guest)


@router.delete("/{guest_id}", status_code=204)
async def delete_guest(
    guest_id: str,
) -> None:
    """
    Delete a guest.
    """
    await GuestWriteService.delete_guest(guest_id)


@router.post("/{guest_id}/invite", response_model=InviteGuestResponse)
async def invite_guest(
    guest_id: str,
    background_tasks: BackgroundTasks,
) -> InviteGuestResponse:
    """
    Send an invitation email to a guest.
    """
    guest = await GuestReadService.get_guest(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    # Pass IDs to background task, not session
    background_tasks.add_task(GuestWriteService.send_invitation, guest_id, guest.event_id)

    return InviteGuestResponse(
        message="Invitation sent successfully",
        guest_id=guest.id,
        email=guest.email,
    )
