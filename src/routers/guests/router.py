from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.routers.guests.schemas import (
    GuestCreate,
    GuestUpdate,
    GuestResponse,
    GuestListResponse,
    InviteGuestResponse,
)
from src.routers.guests.service import GuestService
from src.models.guest import GuestStatus
from src.models.event import Event
from sqlalchemy import select


router = APIRouter()


@router.get("/", response_model=GuestListResponse)
async def list_guests(
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    status: Optional[GuestStatus] = Query(None, description="Filter by RSVP status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> GuestListResponse:
    """
    List all guests with optional filtering by event and status.
    """
    guests, total = await GuestService.get_guests(
        db, event_id=event_id, status=status, skip=skip, limit=limit
    )
    return GuestListResponse(
        guests=[GuestResponse.model_validate(g) for g in guests],
        total=total,
    )


@router.post("/", response_model=GuestResponse, status_code=201)
async def create_guest(
    guest_data: GuestCreate,
    db: AsyncSession = Depends(get_db),
) -> GuestResponse:
    """
    Create a new guest.
    """
    # Verify event exists
    event_result = await db.execute(select(Event).where(Event.id == guest_data.event_id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    guest = await GuestService.create_guest(
        db=db,
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
    db: AsyncSession = Depends(get_db),
) -> GuestResponse:
    """
    Get a specific guest by ID.
    """
    guest = await GuestService.get_guest(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return GuestResponse.model_validate(guest)


@router.put("/{guest_id}", response_model=GuestResponse)
async def update_guest(
    guest_id: str,
    guest_data: GuestUpdate,
    db: AsyncSession = Depends(get_db),
) -> GuestResponse:
    """
    Update a guest's information.
    """
    guest = await GuestService.get_guest(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    guest = await GuestService.update_guest(
        db=db,
        guest=guest,
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
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a guest.
    """
    guest = await GuestService.get_guest(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    await GuestService.delete_guest(db, guest)


@router.post("/{guest_id}/invite", response_model=InviteGuestResponse)
async def invite_guest(
    guest_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> InviteGuestResponse:
    """
    Send an invitation email to a guest.
    """
    guest = await GuestService.get_guest(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    event_result = await db.execute(select(Event).where(Event.id == guest.event_id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Send invitation email in background
    background_tasks.add_task(GuestService.send_invitation, db, guest, event)

    return InviteGuestResponse(
        message="Invitation sent successfully",
        guest_id=guest.id,
        email=guest.email,
    )
