import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint returns healthy status."""
    response = await client.get("/healthz/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test the root endpoint returns welcome message."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to the Wedding RSVP API"
