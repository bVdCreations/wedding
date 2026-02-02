from uuid import uuid4

import pytest

from src.guests.dtos import GuestDTO, GuestStatus, RSVPInfoDTO
from src.guests.features.get_guest_info.router import get_rsvp_read_model
from src.guests.repository.read_models import RSVPReadModel
from src.guests.urls import GET_GUEST_INFO_URL


class InMemoryRSVPReadModel(RSVPReadModel):
    """In-memory read model for testing."""

    def __init__(self, guests: list[GuestDTO] = None):
        self._guests: dict[str, GuestDTO] = {}
        if guests:
            for guest in guests:
                self._guests[guest.token] = guest

    async def get_rsvp_info(self, token: str) -> RSVPInfoDTO | None:
        """Get RSVP info from in-memory storage."""
        guest = self._guests.get(token)
        if not guest:
            return None

        return RSVPInfoDTO(
            token=guest.token,
            name=guest.name,
            event_name="Wedding Celebration",  # Match the real model
            event_date="October 15, 2026 at 3:00 PM",
            event_location="Grand Ballroom",
            status=guest.status,
            is_plus_one=guest.is_plus_one,
            plus_one_name=guest.plus_one_name,
        )


@pytest.mark.asyncio
async def test_get_rsvp_success(client_factory):
    """Test that a valid token returns RSVP page information."""
    guest = GuestDTO(
        id=uuid4(),
        name="John Doe",
        status=GuestStatus.PENDING,
        is_plus_one=False,
        plus_one_name=None,
        email="john@example.com",
    )

    read_model = InMemoryRSVPReadModel([guest])

    overrides = {
        get_rsvp_read_model: lambda: read_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(GET_GUEST_INFO_URL.format(token=guest.token))

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == guest.token
    assert data["guest_name"] == guest.name
    assert data["status"] == GuestStatus.PENDING.value
    assert data["is_plus_one"] is False


@pytest.mark.asyncio
async def test_get_rsvp_invalid_token(
    client_factory,
):
    """Test that an invalid token returns 404."""
    guest = GuestDTO(
        id=uuid4(),
        name="John Doe",
        status=GuestStatus.PENDING,
        is_plus_one=False,
        plus_one_name=None,
        email="john@example.com",
    )

    read_model = InMemoryRSVPReadModel([guest])
    overrides = {
        get_rsvp_read_model: lambda: read_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(GET_GUEST_INFO_URL.format(token="invalid-token-12345"))

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid or expired RSVP link"
