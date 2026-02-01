from unittest.mock import MagicMock

import pytest

from src.email.service import EmailService
from src.models.guest import GuestStatus


@pytest.fixture
def mock_email_service():
    return MagicMock(spec=EmailService)


# GET /rsvp/{token} Tests


@pytest.mark.asyncio
async def test_get_rsvp_success(client_factory, test_guest, mock_email_service):
    """Test that a valid token returns RSVP page information."""
    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.get(f"/rsvp/{test_guest.rsvp_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == test_guest.rsvp_token
    assert data["guest_name"] == test_guest.name
    assert data["status"] == GuestStatus.PENDING.value
    assert data["is_plus_one"] is False


@pytest.mark.asyncio
async def test_get_rsvp_invalid_token(client_factory, mock_email_service):
    """Test that an invalid token returns 404."""
    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.get("/rsvp/invalid-token-12345")

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid or expired RSVP link"


@pytest.mark.asyncio
async def test_get_rsvp_nonexistent_token(client_factory, mock_email_service):
    """Test that a non-existent token returns 404."""
    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.get(f"/rsvp/{'a' * 36}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid or expired RSVP link"


# POST /rsvp/{token}/respond Tests


@pytest.mark.asyncio
async def test_submit_rsvp_attending(client_factory, test_guest, mock_email_service):
    """Test submitting an RSVP with attending=true."""
    rsvp_data = {"attending": True, "plus_one": False, "dietary_requirements": []}

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(f"/rsvp/{test_guest.rsvp_token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value
    assert "Thank you for confirming" in data["message"]

    # Verify email was sent
    assert len(mock_email_service.sent_emails) == 1
    email = mock_email_service.sent_emails[0]
    assert email["attending"] == "Yes"


@pytest.mark.asyncio
async def test_submit_rsvp_not_attending(client_factory, test_guest, mock_email_service):
    """Test submitting an RSVP with attending=false."""
    rsvp_data = {"attending": False, "plus_one": False, "dietary_requirements": []}

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(f"/rsvp/{test_guest.rsvp_token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is False
    assert data["status"] == GuestStatus.DECLINED.value
    assert "We're sorry you can't make it" in data["message"]

    # Verify email was sent
    assert len(mock_email_service.sent_emails) == 1
    email = mock_email_service.sent_emails[0]
    assert email["attending"] == "No"


@pytest.mark.asyncio
async def test_submit_rsvp_with_dietary_requirements(
    client_factory, test_guest, mock_email_service
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

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(f"/rsvp/{test_guest.rsvp_token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    # Verify email contains dietary info
    assert len(mock_email_service.sent_emails) == 1
    email = mock_email_service.sent_emails[0]
    assert "vegetarian" in email["dietary"]
    assert "gluten_free" in email["dietary"]


@pytest.mark.asyncio
async def test_submit_rsvp_with_plus_one(client_factory, test_guest, mock_email_service):
    """Test submitting an RSVP with plus one."""
    rsvp_data = {
        "attending": True,
        "plus_one": True,
        "plus_one_name": "John Doe",
        "dietary_requirements": [],
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(f"/rsvp/{test_guest.rsvp_token}/respond", json=rsvp_data)

    assert response.status_code == 200
    data = response.json()
    assert data["attending"] is True
    assert data["status"] == GuestStatus.CONFIRMED.value

    # Verify email contains plus one info
    assert len(mock_email_service.sent_emails) == 1
    email = mock_email_service.sent_emails[0]
    assert email["plus_one"] == "Yes"


@pytest.mark.asyncio
async def test_submit_rsvp_invalid_token(client_factory, mock_email_service):
    """Test submitting RSVP with invalid token returns 404."""
    rsvp_data = {"attending": True, "plus_one": False, "dietary_requirements": []}

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post("/rsvp/invalid-token-12345/respond", json=rsvp_data)

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid RSVP token"
