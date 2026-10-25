from contextlib import asynccontextmanager

import pytest
from backend.api.dependencies import get_connection_provider
from backend.api.main import app
from backend.app.ports.database import ConnectionProvider
from fastapi.testclient import TestClient


class HealthyMockConnectionProvider(ConnectionProvider):
    @asynccontextmanager
    async def session(self):
        yield

    async def check_connectivity(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def override_db_dependency():
    app.dependency_overrides[get_connection_provider] = lambda: (
        HealthyMockConnectionProvider()
    )
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://192.168.1.5:8080",
        "http://192.168.1.5:3000",
        "http://192.168.0.100:8000",
        "http://10.0.0.15:3000",
        "http://10.254.254.1:8080",
        "http://172.16.0.1:8080",
        "http://172.24.10.5:3000",
        "http://172.31.255.254:8080",
        "https://192.168.1.50:8443",
    ],
)
def test_cors_preflight_allowed_origins(client: TestClient, origin: str):
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "GET" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.parametrize(
    "disallowed_origin",
    [
        "http://malicious.example.com",
        "https://evil-site.org",
        "http://8.8.8.8:8000",
        "http://1.1.1.1:8080",
        "http://172.15.0.1:8000",  # Below RFC-1918 172.16.0.0/12
        "http://172.32.0.1:8000",  # Above RFC-1918 172.31.255.255
    ],
)
def test_cors_preflight_disallowed_origins(client: TestClient, disallowed_origin: str):
    headers = {
        "Origin": disallowed_origin,
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/health", headers=headers)
    # CORSMiddleware does not attach CORS headers for disallowed origins
    assert "access-control-allow-origin" not in response.headers


def test_cors_simple_request_allowed_origin(client: TestClient):
    origin = "http://192.168.1.5:8080"
    response = client.get("/api/v1/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
