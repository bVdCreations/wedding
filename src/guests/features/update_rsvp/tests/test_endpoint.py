from typing import TYPE_CHECKING

import pytest

from src.guests.dtos import GuestStatus, RSVPResponseDTO

if TYPE_CHECKING:
    from src.guests.features.update_rsvp.router import RSVPResponseSubmit
from src.guests.features.update_rsvp.router import get_rsvp_write_model
from src.guests.repository.write_models import RSVPWriteModel
from src.guests.urls import UPDATE_RSVP_URL


class InMemoryRSVPWriteModel(RSVPWriteModel):
    """In-memory write model for testing."""

    def __init__(
        self,
        memory: dict,
    ):
        self._memory = memory

    async def submit_rsvp(
        self,
        token: str,
        rsvp_data: "RSVPResponseSubmit",
    ) -> RSVPResponseDTO:
        self._memory[token] = rsvp_data.model_dump()

        attending = rsvp_data.attending
        status = GuestStatus.CONFIRMED if attending else GuestStatus.DECLINED
        message = (
            "Thank you for confirming your attendance!"
            if attending
            else "We're sorry you can't make it. Your response has been recorded."
        )
        return RSVPResponseDTO(
            message=message,
            attending=attending,
            status=status,
        )


@pytest.mark.asyncio
async def test_submit_rsvp_attending(client_factory):
    memory = {}
    token = "test-token-12345"
    write_model = InMemoryRSVPWriteModel(memory)
    """Test submitting an RSVP with attending=true."""
    rsvp_data = {"attending": True, "family_member_updates": {}}
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value
    assert "Thank you for confirming" in data["message"]


@pytest.mark.asyncio
async def test_submit_rsvp_not_attending(client_factory):
    memory = {}
    token = "test-token-12345"
    write_model = InMemoryRSVPWriteModel(memory)
    rsvp_data = {"attending": False, "family_member_updates": {}}
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is False
    assert data["status"] == GuestStatus.DECLINED.value
    assert "We're sorry you can't make it" in data["message"]


@pytest.mark.asyncio
async def test_submit_rsvp_with_dietary_requirements(client_factory):
    """Test submitting an RSVP with dietary requirements."""

    memory = {}
    token = "test-token-12345"
    write_model = InMemoryRSVPWriteModel(memory)
    rsvp_data = {
        "attending": True,
        "guest_info": {
            "first_name": "Test",
            "last_name": "Guest",
            "dietary_requirements": [
                {"requirement_type": "vegetarian", "notes": "No mushrooms please"},
                {"requirement_type": "gluten_free", "notes": None},
            ],
        },
        "family_member_updates": {},
    }
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value


@pytest.mark.asyncio
async def test_submit_rsvp_with_guest_info_allergies(client_factory):
    """Test that allergies are passed through guest_info."""

    memory = {}
    token = "test-token-guest-allergies"
    write_model = InMemoryRSVPWriteModel(memory)
    rsvp_data = {
        "attending": True,
        "family_member_updates": {},
        "guest_info": {
            "first_name": "Alice",
            "last_name": "Smith",
            "phone": None,
            "allergies": "Nuts and dairy",
        },
    }
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    assert memory[token]["guest_info"]["allergies"] == "Nuts and dairy"


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one(client_factory):
    """Test submitting an RSVP with plus one."""

    memory = {}
    token = "test-token-12345"
    write_model = InMemoryRSVPWriteModel(memory)
    rsvp_data = {
        "attending": True,
        "plus_one_details": {
            "email": "plusone@example.com",
            "first_name": "John",
            "last_name": "Doe",
        },
        "family_member_updates": {},
    }
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    assert memory[token]["plus_one_details"] == {
        "email": "plusone@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "allergies": None,
        "dietary_requirements": [],
    }


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one_allergies(client_factory):
    """Test submitting an RSVP with plus one including allergies."""

    memory = {}
    token = "test-token-allergies"
    write_model = InMemoryRSVPWriteModel(memory)
    rsvp_data = {
        "attending": True,
        "plus_one_details": {
            "email": "plusone@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "allergies": "Peanuts and shellfish",
        },
        "family_member_updates": {},
    }
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    assert memory[token]["plus_one_details"]["allergies"] == "Peanuts and shellfish"


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one_dietary_requirements(client_factory):
    """Test submitting an RSVP with plus one including dietary requirements."""

    memory = {}
    token = "test-token-dietary"
    write_model = InMemoryRSVPWriteModel(memory)
    rsvp_data = {
        "attending": True,
        "plus_one_details": {
            "email": "plusone@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "dietary_requirements": [
                {"requirement_type": "vegetarian", "notes": None},
                {"requirement_type": "other", "notes": "No spicy food"},
            ],
        },
        "family_member_updates": {},
    }
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    # Verify dietary requirements are passed through
    assert "dietary_requirements" in memory[token]["plus_one_details"]
    dietary_reqs = memory[token]["plus_one_details"]["dietary_requirements"]
    assert len(dietary_reqs) == 2
    assert dietary_reqs[0]["requirement_type"] == "vegetarian"
    assert dietary_reqs[1]["requirement_type"] == "other"
    assert dietary_reqs[1]["notes"] == "No spicy food"


@pytest.mark.asyncio
async def test_submit_rsvp_family_member_allergies_in_guest_info(client_factory):
    """Test that family member allergies and dietary requirements are passed through guest_info."""

    memory = {}
    token = "test-token-family-allergies"
    write_model = InMemoryRSVPWriteModel(memory)
    family_uuid = "11111111-1111-1111-1111-111111111111"
    rsvp_data = {
        "attending": True,
        "family_member_updates": {
            family_uuid: {
                "attending": True,
                "guest_info": {
                    "first_name": "Bob",
                    "last_name": "Jones",
                    "phone": None,
                    "allergies": "Sesame",
                    "dietary_requirements": [{"requirement_type": "vegetarian", "notes": None}],
                },
            }
        },
    }
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    family_update = memory[token]["family_member_updates"][family_uuid]
    assert family_update["guest_info"]["allergies"] == "Sesame"
    assert family_update["guest_info"]["dietary_requirements"][0]["requirement_type"] == "vegetarian"


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one_allergies_and_dietary(client_factory):
    """Test submitting an RSVP with plus one including both allergies and dietary requirements."""

    memory = {}
    token = "test-token-both"
    write_model = InMemoryRSVPWriteModel(memory)
    rsvp_data = {
        "attending": True,
        "plus_one_details": {
            "email": "plusone@example.com",
            "first_name": "Maria",
            "last_name": "Garcia",
            "allergies": "Gluten",
            "dietary_requirements": [
                {"requirement_type": "vegan", "notes": None},
            ],
        },
        "family_member_updates": {},
    }
    overrides = {
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=UPDATE_RSVP_URL.format(token=token), json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    # Verify both allergies and dietary requirements are passed through
    plus_one_details = memory[token]["plus_one_details"]
    assert plus_one_details["allergies"] == "Gluten"
    assert len(plus_one_details["dietary_requirements"]) == 1
    assert plus_one_details["dietary_requirements"][0]["requirement_type"] == "vegan"
