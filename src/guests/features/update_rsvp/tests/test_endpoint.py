from dataclasses import asdict
from typing import Dict
from uuid import UUID

import pytest

from src.guests.dtos import (
    FamilyMemberUpdateDTO,
    GuestInfoUpdateDTO,
    GuestStatus,
    PlusOneDTO,
    RSVPResponseDTO,
)
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
        attending: bool,
        plus_one_details: PlusOneDTO | None,
        dietary_requirements: list[dict],
        guest_info: GuestInfoUpdateDTO | None = None,
        family_member_updates: Dict[UUID, FamilyMemberUpdateDTO] | None = None,
    ) -> RSVPResponseDTO:
        self._memory[token] = {
            "attending": attending,
            "plus_one_details": plus_one_details,
            "dietary_requirements": dietary_requirements,
            "guest_info": guest_info,
            "family_member_updates": family_member_updates,
        }

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
    rsvp_data = {"attending": True, "dietary_requirements": [], "family_member_updates": {}}
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
    rsvp_data = {"attending": False, "dietary_requirements": [], "family_member_updates": {}}
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
        "dietary_requirements": [
            {"requirement_type": "vegetarian", "notes": "No mushrooms please"},
            {"requirement_type": "gluten_free", "notes": None},
        ],
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
        "dietary_requirements": [],
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

    assert asdict(memory[token]["plus_one_details"]) == {
        "email": "plusone@example.com",
        "first_name": "John",
        "last_name": "Doe",
    }
