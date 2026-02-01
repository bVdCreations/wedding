from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app


@asynccontextmanager
async def _async_client_override_factory(
    overrides: dict[Callable[..., Any], Callable[..., Any]] = {},
):
    app.dependency_overrides = overrides

    transport = ASGITransport(app=app)
    client_generator = AsyncClient(transport=transport, base_url="http://0.0.0.0:8500")
    yield client_generator
    app.dependency_overrides = {}


@pytest.fixture()
def client_factory():
    return _async_client_override_factory


@pytest_asyncio.fixture(scope="session")
async def client():
    async with _async_client_override_factory({}) as client:
        yield client
