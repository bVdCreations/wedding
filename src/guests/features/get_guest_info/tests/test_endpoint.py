from uuid import uuid4

import pytest

from src.guests.dtos import RSVPDTO, GuestDTO, GuestStatus, RSVPInfoDTO
from src.guests.features.get_guest_info.router import get_rsvp_read_model
from src.guests.repository.read_models import RSVPReadModel
from src.guests.urls import GET_GUEST_INFO_URL


class InMemoryRSVPReadModel(RSVPReadModel):
    """In-memory read model for testing."""

    def __init__(self, guests: list[GuestDTO] = None):
        self._guests: dict[str, GuestDTO] = {}
        if guests:
            for guest in guests:
                self._guests[guest.rsvp.token] = guest

    async def get_rsvp_info(self, token: str) -> RSVPInfoDTO | None:
        """Get RSVP info from in-memory storage."""
        guest = self._guests.get(token)
        if not guest:
            return None

        # Calculate attending from status
        if guest.rsvp.status == GuestStatus.CONFIRMED:
            attending = True
        elif guest.rsvp.status == GuestStatus.DECLINED:
            attending = False
        else:
            attending = None

        return RSVPInfoDTO(
            guest_uuid=guest.id,
            token=guest.rsvp.token,
            first_name=guest.first_name or "",
            last_name=guest.last_name or "",
            phone=guest.phone,
            status=guest.rsvp.status,
            plus_one_of_id=guest.plus_one_of_id,
            family_id=guest.family_id,
            family_members=[],
            plus_one_email=None,
            plus_one_first_name=None,
            plus_one_last_name=None,
            attending=attending,
            dietary_requirements=[],
        )


class InMemoryRSVPReadModelWithDietary(RSVPReadModel):
    """In-memory read model with dietary requirements for testing."""

    def __init__(
        self,
        guests: list[GuestDTO] = None,
        plus_one_email: str = None,
        plus_one_first_name: str = None,
        plus_one_last_name: str = None,
    ):
        self._guests: dict[str, GuestDTO] = {}
        self._plus_one_email = plus_one_email
        self._plus_one_first_name = plus_one_first_name
        self._plus_one_last_name = plus_one_last_name
        if guests:
            for guest in guests:
                self._guests[guest.rsvp.token] = guest

    async def get_rsvp_info(self, token: str) -> RSVPInfoDTO | None:
        """Get RSVP info from in-memory storage with dietary requirements."""
        guest = self._guests.get(token)
        if not guest:
            return None

        # Calculate attending from status
        if guest.rsvp.status == GuestStatus.CONFIRMED:
            attending = True
        elif guest.rsvp.status == GuestStatus.DECLINED:
            attending = False
        else:
            attending = None

        return RSVPInfoDTO(
            guest_uuid=guest.id,
            token=guest.rsvp.token,
            first_name=guest.first_name or "",
            last_name=guest.last_name or "",
            phone=guest.phone,
            status=guest.rsvp.status,
            plus_one_of_id=guest.plus_one_of_id,
            family_id=guest.family_id,
            family_members=[],
            plus_one_email=self._plus_one_email,
            plus_one_first_name=self._plus_one_first_name,
            plus_one_last_name=self._plus_one_last_name,
            attending=attending,
            dietary_requirements=[
                {"requirement_type": "vegetarian", "notes": None},
                {"requirement_type": "gluten_free", "notes": "Minor allergy"},
            ],
        )


@pytest.mark.asyncio
async def test_get_rsvp_success(client_factory):
    """Test that a valid token returns RSVP page information with prefill data."""
    token = str(uuid4())
    guest_id = uuid4()
    guest = GuestDTO(
        id=guest_id,
        email="john@example.com",
        rsvp=RSVPDTO(
            status=GuestStatus.PENDING,
            token=token,
            link=f"http://localhost:4321/rsvp/?token={token}",
        ),
        first_name="John",
        last_name="Doe",
        plus_one_of_id=None,
    )

    read_model = InMemoryRSVPReadModel([guest])

    overrides = {
        get_rsvp_read_model: lambda: read_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(GET_GUEST_INFO_URL.format(token=token))

    assert response.status_code == 200
    data = response.json()
    # New response format with first_name and last_name
    assert data["guest_uuid"] == str(guest_id)
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["status"] == GuestStatus.PENDING.value
    assert data["is_plus_one"] is False
    assert data["is_family_member"] is False
    assert data["family_id"] is None
    assert data["attending"] is None
    assert data["dietary_requirements"] == []


@pytest.mark.asyncio
async def test_get_rsvp_confirmed_with_dietary(client_factory):
    """Test that confirmed RSVP returns attending=true with dietary requirements."""
    token = str(uuid4())
    guest_id = uuid4()
    original_guest_id = uuid4()
    guest = GuestDTO(
        id=guest_id,
        email="john@example.com",
        rsvp=RSVPDTO(
            status=GuestStatus.CONFIRMED,
            token=token,
            link=f"http://localhost:4321/rsvp/?token={token}",
        ),
        first_name="John",
        last_name="Doe",
        plus_one_of_id=original_guest_id,
    )

    read_model = InMemoryRSVPReadModelWithDietary(
        [guest],
        plus_one_email="jane@example.com",
        plus_one_first_name="Jane",
        plus_one_last_name="Smith",
    )

    overrides = {
        get_rsvp_read_model: lambda: read_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(GET_GUEST_INFO_URL.format(token=token))

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["is_plus_one"] is True
    # Plus one is nested
    assert data["plus_one"]["email"] == "jane@example.com"
    assert data["plus_one"]["first_name"] == "Jane"
    assert data["plus_one"]["last_name"] == "Smith"
    assert len(data["dietary_requirements"]) == 2
    dietary_types = [req["requirement_type"] for req in data["dietary_requirements"]]
    assert "vegetarian" in dietary_types
    assert "gluten_free" in dietary_types


@pytest.mark.asyncio
async def test_get_rsvp_declined(client_factory):
    """Test that declined RSVP returns attending=false."""
    token = str(uuid4())
    guest_id = uuid4()
    guest = GuestDTO(
        id=guest_id,
        email="john@example.com",
        rsvp=RSVPDTO(
            status=GuestStatus.DECLINED,
            token=token,
            link=f"http://localhost:4321/rsvp/?token={token}",
        ),
        first_name="Jane",
        last_name="Doe",
        plus_one_of_id=None,
    )

    read_model = InMemoryRSVPReadModel([guest])

    overrides = {
        get_rsvp_read_model: lambda: read_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(GET_GUEST_INFO_URL.format(token=token))

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is False


@pytest.mark.asyncio
async def test_get_rsvp_invalid_token(
    client_factory,
):
    """Test that an invalid token returns 404."""
    token = str(uuid4())
    guest_id = uuid4()
    guest = GuestDTO(
        id=guest_id,
        email="john@example.com",
        rsvp=RSVPDTO(
            status=GuestStatus.PENDING,
            token=token,
            link=f"http://localhost:4321/rsvp/?token={token}",
        ),
        first_name="John",
        last_name="Doe",
        plus_one_of_id=None,
    )

    read_model = InMemoryRSVPReadModel([guest])
    overrides = {
        get_rsvp_read_model: lambda: read_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(GET_GUEST_INFO_URL.format(token="invalid-token-12345"))

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid or expired RSVP link"
