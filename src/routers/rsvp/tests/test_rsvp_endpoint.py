import pytest

from src.models.guest import GuestStatus
from src.routers.rsvp.router import get_rsvp_read_model, get_rsvp_write_model
from src.routers.rsvp.tests.inmemory_models import (
    InMemoryEmailService,
    create_test_guest,
    create_test_read_model,
    create_test_write_model,
)


@pytest.fixture
def inmemory_email_service():
    """Create a fresh in-memory email service for each test."""
    return InMemoryEmailService()


@pytest.fixture
def test_guest():
    """Create a test guest fixture."""
    return create_test_guest(
        token="test-token-12345",
        name="John Doe",
        email="john@example.com",
    )


@pytest.fixture
def read_model(test_guest):
    """Create an in-memory read model with a test guest."""
    return create_test_read_model(guests=[test_guest])


@pytest.fixture
def write_model(read_model, inmemory_email_service):
    """Create an in-memory write model with read model and email service."""
    return create_test_write_model(
        read_model=read_model,
        email_service=inmemory_email_service,
    )


@pytest.fixture
def empty_read_model():
    """Create an in-memory read model with no guests."""
    return create_test_read_model(guests=[])


@pytest.fixture
def empty_write_model(empty_read_model, inmemory_email_service):
    """Create an in-memory write model with empty read model."""
    return create_test_write_model(
        read_model=empty_read_model,
        email_service=inmemory_email_service,
    )


# GET /rsvp/{token} Tests


@pytest.mark.asyncio
async def test_get_rsvp_success(client_factory, test_guest, read_model, write_model):
    """Test that a valid token returns RSVP page information."""

    overrides = {
        get_rsvp_read_model: lambda: read_model,
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(f"/rsvp/{test_guest.token}")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == test_guest.token
    assert data["guest_name"] == test_guest.name
    assert data["status"] == GuestStatus.PENDING.value
    assert data["is_plus_one"] is False


@pytest.mark.asyncio
async def test_get_rsvp_invalid_token(client_factory, read_model, write_model):
    """Test that an invalid token returns 404."""
    overrides = {
        get_rsvp_read_model: lambda: read_model,
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get("/rsvp/invalid-token-12345")

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid or expired RSVP link"


@pytest.mark.asyncio
async def test_get_rsvp_nonexistent_token(client_factory, read_model, write_model):
    """Test that a non-existent token returns 404."""
    overrides = {
        get_rsvp_read_model: lambda: read_model,
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.get(f"/rsvp/{'a' * 36}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid or expired RSVP link"


# POST /rsvp/{token}/respond Tests


@pytest.mark.asyncio
async def test_submit_rsvp_attending(
    client_factory, test_guest, read_model, write_model, inmemory_email_service
):
    """Test submitting an RSVP with attending=true."""
    rsvp_data = {"attending": True, "plus_one": False, "dietary_requirements": []}
    overrides = {
        get_rsvp_read_model: lambda: read_model,
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(f"/rsvp/{test_guest.token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value
    assert "Thank you for confirming" in data["message"]

    # Verify email was sent
    assert len(inmemory_email_service.sent_emails) == 1
    email = inmemory_email_service.sent_emails[0]
    assert email["attending"] == "Yes"


@pytest.mark.asyncio
async def test_submit_rsvp_not_attending(
    client_factory, test_guest, read_model, write_model, inmemory_email_service
):
    """Test submitting an RSVP with attending=false."""
    rsvp_data = {"attending": False, "plus_one": False, "dietary_requirements": []}
    overrides = {
        get_rsvp_read_model: lambda: read_model,
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(f"/rsvp/{test_guest.token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is False
    assert data["status"] == GuestStatus.DECLINED.value
    assert "We're sorry you can't make it" in data["message"]

    # Verify email was sent
    assert len(inmemory_email_service.sent_emails) == 1
    email = inmemory_email_service.sent_emails[0]
    assert email["attending"] == "No"


@pytest.mark.asyncio
async def test_submit_rsvp_with_dietary_requirements(
    client_factory, test_guest, read_model, write_model, inmemory_email_service
):
    """Test submitting an RSVP with dietary requirements."""
    rsvp_data = {
        "attending": True,
        "plus_one": False,
        "dietary_requirements": [
            {"requirement_type": "vegetarian", "notes": "No mushrooms please"},
            {"requirement_type": "gluten_free", "notes": None},
        ],
    }
    overrides = {
        get_rsvp_read_model: lambda: read_model,
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(f"/rsvp/{test_guest.token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    # Verify email contains dietary info
    assert len(inmemory_email_service.sent_emails) == 1
    email = inmemory_email_service.sent_emails[0]
    assert "vegetarian" in email["dietary"]
    assert "gluten_free" in email["dietary"]


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one(
    client_factory, test_guest, read_model, write_model, inmemory_email_service
):
    """Test submitting an RSVP with plus one."""
    rsvp_data = {
        "attending": True,
        "plus_one": True,
        "plus_one_name": "John Doe",
        "dietary_requirements": [],
    }
    overrides = {
        get_rsvp_read_model: lambda: read_model,
        get_rsvp_write_model: lambda: write_model,
    }

    async with client_factory(overrides) as client:
        response = await client.post(f"/rsvp/{test_guest.token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    # Verify email contains plus one info
    assert len(inmemory_email_service.sent_emails) == 1
    email = inmemory_email_service.sent_emails[0]
    assert email["plus_one"] == "Yes"
