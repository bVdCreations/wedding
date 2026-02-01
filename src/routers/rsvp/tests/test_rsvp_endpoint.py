import pytest
from httpx import AsyncClient
from src.models.guest import GuestStatus
from src.models.dietary import DietaryType


# GET /rsvp/{token} Tests


@pytest.mark.asyncio
async def test_get_rsvp_success(
    client_factory, test_guest, test_event, mock_email_service
):
    """Test that a valid token returns RSVP page information."""
    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.get(f"/rsvp/{test_guest.rsvp_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == test_guest.rsvp_token
    assert data["guest_name"] == test_guest.name
    assert data["event_name"] == test_event.name
    assert data["status"] == GuestStatus.PENDING.value
    assert data["is_plus_one"] is False
    assert data["event_location"] == test_event.location


@pytest.mark.asyncio
async def test_get_rsvp_invalid_token(client_factory, test_event, mock_email_service):
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
async def test_submit_rsvp_attending(
    client_factory, test_guest, test_event, mock_email_service
):
    """Test submitting an RSVP with attending=true."""
    rsvp_data = {
        "attending": True,
        "plus_one": False,
        "dietary_requirements": []
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(
            f"/rsvp/{test_guest.rsvp_token}/respond",
            json=rsvp_data
        )

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
async def test_submit_rsvp_not_attending(
    client_factory, test_guest, test_event, mock_email_service
):
    """Test submitting an RSVP with attending=false."""
    rsvp_data = {
        "attending": False,
        "plus_one": False,
        "dietary_requirements": []
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(
            f"/rsvp/{test_guest.rsvp_token}/respond",
            json=rsvp_data
        )

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
    client_factory, test_guest, test_event, mock_email_service
):
    """Test submitting an RSVP with dietary requirements."""
    rsvp_data = {
        "attending": True,
        "plus_one": False,
        "dietary_requirements": [
            {"requirement_type": "vegetarian", "notes": "No mushrooms please"},
            {"requirement_type": "gluten_free", "notes": None}
        ]
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(
            f"/rsvp/{test_guest.rsvp_token}/respond",
            json=rsvp_data
        )

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
async def test_submit_rsvp_with_plus_one(
    client_factory, test_guest, test_event, mock_email_service
):
    """Test submitting an RSVP with plus one."""
    rsvp_data = {
        "attending": True,
        "plus_one": True,
        "plus_one_name": "John Doe",
        "dietary_requirements": []
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(
            f"/rsvp/{test_guest.rsvp_token}/respond",
            json=rsvp_data
        )

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
    rsvp_data = {
        "attending": True,
        "plus_one": False,
        "dietary_requirements": []
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(
            "/rsvp/invalid-token-12345/respond",
            json=rsvp_data
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid RSVP token"


@pytest.mark.asyncio
async def test_submit_rsvp_clears_old_dietary(
    client_factory, test_guest_with_dietary, test_event, mock_email_service, db
):
    """Test that submitting new RSVP clears old dietary requirements."""
    # Verify guest has existing dietary requirement
    from src.models.dietary import DietaryOption
    result = await db.execute(
        DietaryOption.__table__.select().where(DietaryOption.guest_id == test_guest_with_dietary.id)
    )
    old_dietary = result.fetchall()
    assert len(old_dietary) == 1
    assert old_dietary[0][2] == "vegetarian"  # requirement_type

    # Submit new RSVP with different dietary requirements
    rsvp_data = {
        "attending": True,
        "plus_one": False,
        "dietary_requirements": [
            {"requirement_type": "vegan", "notes": "No animal products"}
        ]
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(
            f"/rsvp/{test_guest_with_dietary.rsvp_token}/respond",
            json=rsvp_data
        )

    assert response.status_code == 200

    # Verify old dietary requirements are cleared and new ones are added
    result = await db.execute(
        DietaryOption.__table__.select().where(DietaryOption.guest_id == test_guest_with_dietary.id)
    )
    updated_dietary = result.fetchall()
    assert len(updated_dietary) == 1
    assert updated_dietary[0][2] == "vegan"  # requirement_type is now vegan


@pytest.mark.asyncio
async def test_submit_rsvp_not_attending_clears_plus_one(
    client_factory, test_guest, test_event, mock_email_service, db
):
    """Test that submitting not attending clears plus one name."""
    # First, set the guest as attending with plus one
    test_guest.is_plus_one = True
    test_guest.plus_one_name = "Jane Doe"
    test_guest.status = GuestStatus.CONFIRMED
    await db.commit()

    # Submit RSVP as not attending
    rsvp_data = {
        "attending": False,
        "plus_one": False,
        "dietary_requirements": []
    }

    async with client_factory(
        {"src.routers.rsvp.router.get_email_service": lambda: mock_email_service}
    ) as client:
        response = await client.post(
            f"/rsvp/{test_guest.rsvp_token}/respond",
            json=rsvp_data
        )

    assert response.status_code == 200

    # Refresh guest from database
    await db.refresh(test_guest)

    # Verify plus one is cleared
    assert test_guest.is_plus_one is False
    assert test_guest.plus_one_name is None
    assert test_guest.status == GuestStatus.DECLINED
