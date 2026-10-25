import pytest
from backend.api.main import app
from fastapi.testclient import TestClient

INSECURE_KEYS = [
    "",
    "changeme",
    "changeme_secret_key",
    "secret",
    "a" * 31,
]


@pytest.mark.parametrize("secret_key", INSECURE_KEYS)
def test_production_rejects_insecure_secret_key(monkeypatch, secret_key):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", secret_key)

    with (
        pytest.raises(RuntimeError, match="Insecure SECRET_KEY configured"),
        TestClient(app),
    ):
        pass


def test_production_rejects_missing_secret_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with (
        pytest.raises(RuntimeError, match="Insecure SECRET_KEY configured"),
        TestClient(app),
    ):
        pass


def test_production_accepts_strong_secret_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)

    with TestClient(app):
        pass


@pytest.mark.parametrize("environment", ["development", "test", None])
def test_non_production_allows_trivial_secret_key(monkeypatch, environment):
    if environment is None:
        monkeypatch.delenv("ENVIRONMENT", raising=False)
    else:
        monkeypatch.setenv("ENVIRONMENT", environment)
    monkeypatch.setenv("SECRET_KEY", "changeme")

    with TestClient(app):
        pass
