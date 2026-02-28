"""Tests for request invitation endpoint."""

import pytest

from src.guests.features.request_invitation.dtos import RequestInvitationResponse
from src.guests.features.request_invitation.router import (
    REQUEST_INVITATION_URL,
    get_request_invitation_write_model,
)
from src.guests.features.request_invitation.write_model import (
    RequestInvitationWriteModel,
)


class InMemoryRequestInvitationWriteModel(RequestInvitationWriteModel):
    """In-memory write model for testing."""

    def __init__(self, memory: dict):
        self._memory = memory

    async def request_invitation(
        self,
        email: str,
        first_name: str,
        last_name: str,
        language=None,
    ) -> RequestInvitationResponse:
        """Request or resend an invitation email."""
        self._memory["last_request"] = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "language": language,
        }

        # Simulate the response
        return RequestInvitationResponse(
            message="Check your email for your invitation link"
        )


@pytest.mark.asyncio
async def test_request_invitation_new_guest(client_factory):
    """Test requesting invitation for a new guest."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "email": "newguest@example.com",
        "first_name": "John",
        "last_name": "Doe",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Check your email for your invitation link"
    assert memory["last_request"]["email"] == "newguest@example.com"
    assert memory["last_request"]["first_name"] == "John"
    assert memory["last_request"]["last_name"] == "Doe"


@pytest.mark.asyncio
async def test_request_invitation_existing_guest(client_factory):
    """Test requesting invitation for an existing guest."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "email": "existing@example.com",
        "first_name": "Jane",
        "last_name": "Smith",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Check your email for your invitation link"


@pytest.mark.asyncio
async def test_request_invitation_invalid_email(client_factory):
    """Test requesting invitation with invalid email format."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "email": "not-an-email",
        "first_name": "John",
        "last_name": "Doe",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_request_invitation_missing_email(client_factory):
    """Test requesting invitation with missing email."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "first_name": "John",
        "last_name": "Doe",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_request_invitation_missing_first_name(client_factory):
    """Test requesting invitation with missing first name."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "email": "test@example.com",
        "last_name": "Doe",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_request_invitation_missing_last_name(client_factory):
    """Test requesting invitation with missing last name."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "email": "test@example.com",
        "first_name": "John",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_request_invitation_with_language(client_factory):
    """Test requesting invitation with language specified."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "email": "spanish@example.com",
        "first_name": "Juan",
        "last_name": "García",
        "language": "es",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Check your email for your invitation link"
    assert memory["last_request"]["language"] == "es"


@pytest.mark.asyncio
async def test_request_invitation_without_language_defaults_to_english(client_factory):
    """Test requesting invitation without language defaults to English."""
    memory = {}
    write_model = InMemoryRequestInvitationWriteModel(memory)

    request_data = {
        "email": "nolang@example.com",
        "first_name": "John",
        "last_name": "Doe",
    }

    overrides = {
        get_request_invitation_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(url=REQUEST_INVITATION_URL, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Check your email for your invitation link"
    assert memory["last_request"]["language"] is None
