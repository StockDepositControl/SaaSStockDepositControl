from contextlib import asynccontextmanager

from backend.api.dependencies import get_connection_provider
from backend.api.main import app
from backend.app.exceptions import (
    BusinessRuleViolationException,
    DomainException,
    EntityNotFoundException,
)
from backend.app.ports.database import ConnectionProvider
from fastapi.testclient import TestClient


# Registers test routes directly on the app instance for test coverage of domain
# exceptions
@app.get("/test-not-found")
async def trigger_not_found():
    raise EntityNotFoundException("Item not found")


@app.get("/test-business-rule")
async def trigger_business_rule():
    raise BusinessRuleViolationException("Rule violated")


@app.get("/test-generic-domain")
async def trigger_generic_domain():
    raise DomainException("Generic error")


# --- Mock Database Connections ---


class HealthyMockConnectionProvider(ConnectionProvider):
    @asynccontextmanager
    async def session(self):
        yield  # Not used by health endpoint

    async def check_connectivity(self) -> bool:
        return True


class UnhealthyMockConnectionProvider(ConnectionProvider):
    @asynccontextmanager
    async def session(self):
        yield  # Not used by health endpoint

    async def check_connectivity(self) -> bool:
        raise ConnectionRefusedError("Connection refused by host")


# --- Test Cases ---


def test_health_endpoint_healthy():
    # Arrange: Override connection provider dependency with healthy mock
    app.dependency_overrides[get_connection_provider] = lambda: (
        HealthyMockConnectionProvider()
    )
    client = TestClient(app)

    # Act: Request health endpoint
    response = client.get("/health")

    # Assert: Should return 200 with connected status
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"
    app.dependency_overrides.clear()


def test_health_endpoint_unhealthy():
    # Arrange: Override connection provider dependency with unhealthy mock
    app.dependency_overrides[get_connection_provider] = lambda: (
        UnhealthyMockConnectionProvider()
    )
    client = TestClient(app)

    # Act: Request health endpoint
    response = client.get("/health")

    # Assert: Should return 503 Service Unavailable
    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"
    assert response.json()["detail"] == "Database connectivity probe failed"
    assert "Connection refused" not in response.text
    app.dependency_overrides.clear()


def test_exception_handler_entity_not_found():
    client = TestClient(app)
    response = client.get("/test-not-found")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Item not found",
        "error_type": "EntityNotFound",
    }


def test_exception_handler_business_rule_violation():
    client = TestClient(app)
    response = client.get("/test-business-rule")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Rule violated",
        "error_type": "BusinessRuleViolation",
    }


def test_exception_handler_generic_domain_error():
    client = TestClient(app)
    response = client.get("/test-generic-domain")
    assert response.status_code == 500
    assert response.json() == {
        "detail": "Generic error",
        "error_type": "InternalDomainError",
    }
