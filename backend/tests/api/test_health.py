from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies import get_connection_provider
from backend.app.ports.database import LOGICAL_DATABASES as DATABASES, ConnectionProvider


class FakeMultiDbProvider(ConnectionProvider):
    def __init__(self, statuses=None, error=None):
        self._statuses = statuses or {name: True for name in DATABASES}
        self._error = error

    @asynccontextmanager
    async def session(self):
        yield

    async def check_connectivity(self) -> bool:
        return all((await self.check_databases()).values())

    async def check_databases(self) -> dict[str, bool]:
        if self._error:
            raise self._error
        return dict(self._statuses)


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def _use(provider):
    app.dependency_overrides[get_connection_provider] = lambda: provider


def test_health_reports_all_three_databases_connected(client):
    _use(FakeMultiDbProvider())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["databases"] == {name: "connected" for name in DATABASES}
    assert body["version"] == "1.0.0"


def test_health_keeps_legacy_database_key_when_healthy(client):
    _use(FakeMultiDbProvider())

    assert client.get("/api/v1/health").json()["database"] == "connected"


@pytest.mark.parametrize("down", DATABASES)
def test_health_returns_503_when_any_database_is_down(client, down):
    statuses = {name: name != down for name in DATABASES}
    _use(FakeMultiDbProvider(statuses))

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["database"] == "disconnected"
    expected = {name: ("disconnected" if name == down else "connected") for name in DATABASES}
    assert body["databases"] == expected
    assert body["version"] == "1.0.0"


def test_health_returns_503_when_probe_raises(client):
    _use(FakeMultiDbProvider(error=ConnectionRefusedError("Connection refused by host")))

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["database"] == "disconnected"
    assert body["databases"] == {name: "disconnected" for name in DATABASES}
    assert "Connection refused" in body["detail"]


def test_legacy_provider_without_check_databases_still_reports_healthy(client):
    class LegacyProvider(ConnectionProvider):
        @asynccontextmanager
        async def session(self):
            yield

        async def check_connectivity(self) -> bool:
            return True

    _use(LegacyProvider())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"
