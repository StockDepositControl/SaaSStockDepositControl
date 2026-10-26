"""
Behavioural tests for scripts/devops/verify-local-package.sh (stub docker/curl).
"""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
VERIFY = ROOT / "scripts" / "devops" / "verify-local-package.sh"

HEALTHY = (
    '{"status":"healthy","database":"connected","databases":'
    '{"articles":"connected","users":"connected","analytics":"connected"},'
    '"version":"1.0.0"}'
)

DOCKER_STUB = """#!/usr/bin/env bash
echo "docker $*" >> "$CALLS_LOG"
case "$*" in
  *" config "*|*" config") exit "${STUB_COMPOSE_RC:-0}" ;;
esac
"""

CURL_STUB = """#!/usr/bin/env bash
echo "curl $*" >> "$CALLS_LOG"
if [ "${STUB_CURL_RC:-0}" != "0" ]; then
  exit "$STUB_CURL_RC"
fi
printf '%s' "$STUB_HEALTH_BODY"
"""

VALID_ENV = (
    "# on-premise\n"
    "SECRET_KEY=0123456789abcdef0123456789abcdef\n"
    "DB_PASSWORD=s3cret-db-pass\n"
    "HTTP_PORT=8080\n"
    "RUN_MIGRATIONS=true\n"
    "RUN_MIGRATIONS_ARTICLES=false\n"
    "RUN_MIGRATIONS_USERS=true\n"
    "RUN_MIGRATIONS_ANALYTICS=true\n"
)


@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / ".env").write_text(VALID_ENV)
    (root / "docker-compose.yml").write_text("services: {}\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("docker", DOCKER_STUB), ("curl", CURL_STUB)):
        path = bin_dir / name
        path.write_text(body)
        path.chmod(0o755)
    return tmp_path, root


def run_verify(sandbox, env=None):
    tmp_path, root = sandbox
    log = tmp_path / "calls.log"
    full_env = {
        "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}",
        "DEPLOY_ROOT": str(root),
        "CALLS_LOG": str(log),
        "STUB_HEALTH_BODY": HEALTHY,
        **(env or {}),
    }
    result = subprocess.run(
        ["bash", str(VERIFY)],
        env=full_env,
        capture_output=True,
        text=True,
        check=False,
    )
    calls = log.read_text().splitlines() if log.exists() else []
    return result, calls


def test_passes_on_valid_env_and_healthy_stack(sandbox):
    result, calls = run_verify(sandbox)

    assert result.returncode == 0, result.stdout + result.stderr
    health_url = "localhost:8080/api/v1/health"
    assert any(c.startswith("curl ") and health_url in c for c in calls)
    assert any("config -q" in c for c in calls)


def test_fails_when_env_file_is_missing(sandbox):
    _, root = sandbox
    (root / ".env").unlink()

    result, _ = run_verify(sandbox)

    assert result.returncode != 0


def test_fails_on_malformed_env_line(sandbox):
    _, root = sandbox
    (root / ".env").write_text(VALID_ENV + "BROKEN = value\n")

    result, _ = run_verify(sandbox)

    assert result.returncode != 0
    assert "line" in (result.stdout + result.stderr).lower()


def test_fails_when_secret_key_is_empty(sandbox):
    _, root = sandbox
    key_line = "SECRET_KEY=0123456789abcdef0123456789abcdef"
    (root / ".env").write_text(VALID_ENV.replace(key_line, "SECRET_KEY="))

    result, _ = run_verify(sandbox)

    assert result.returncode != 0
    assert "SECRET_KEY" in result.stdout + result.stderr


def test_fails_on_invalid_migration_switch(sandbox):
    _, root = sandbox
    (root / ".env").write_text(
        VALID_ENV.replace(
            "RUN_MIGRATIONS_ARTICLES=false", "RUN_MIGRATIONS_ARTICLES=maybe"
        )
    )

    result, _ = run_verify(sandbox)

    assert result.returncode != 0
    assert "RUN_MIGRATIONS_ARTICLES" in result.stdout + result.stderr


def test_fails_on_non_numeric_http_port(sandbox):
    _, root = sandbox
    (root / ".env").write_text(VALID_ENV.replace("HTTP_PORT=8080", "HTTP_PORT=eighty"))

    result, _ = run_verify(sandbox)

    assert result.returncode != 0
    assert "HTTP_PORT" in result.stdout + result.stderr


def test_fails_when_compose_config_is_invalid(sandbox):
    result, _ = run_verify(sandbox, env={"STUB_COMPOSE_RC": "1"})

    assert result.returncode != 0
    assert "compose" in (result.stdout + result.stderr).lower()


def test_fails_when_health_endpoint_is_unreachable(sandbox):
    result, _ = run_verify(sandbox, env={"STUB_CURL_RC": "22"})

    assert result.returncode != 0
    assert "health" in (result.stdout + result.stderr).lower()


def test_names_the_disconnected_database(sandbox):
    body = HEALTHY.replace(
        '"articles":"connected"', '"articles":"disconnected"'
    ).replace('"status":"healthy"', '"status":"unhealthy"')

    result, _ = run_verify(sandbox, env={"STUB_HEALTH_BODY": body})

    assert result.returncode != 0
    assert "articles" in result.stdout + result.stderr


def test_fails_when_external_articles_database_is_unreachable(sandbox):
    _, root = sandbox
    (root / ".env").write_text(
        VALID_ENV + "ARTICLES_DATABASE_URL="
        "mysql+aiomysql://ro_user:topsecret@127.0.0.1:1/db_articles\n"
    )

    result, _ = run_verify(sandbox)

    assert result.returncode != 0
    assert "127.0.0.1:1" in result.stdout + result.stderr


def test_never_prints_secrets(sandbox):
    _, root = sandbox
    (root / ".env").write_text(
        VALID_ENV + "ARTICLES_DATABASE_URL="
        "mysql+aiomysql://ro_user:topsecret@127.0.0.1:1/db_articles\n"
    )

    result, _ = run_verify(sandbox)
    output = result.stdout + result.stderr

    for secret in ("s3cret-db-pass", "topsecret", "0123456789abcdef"):
        assert secret not in output
