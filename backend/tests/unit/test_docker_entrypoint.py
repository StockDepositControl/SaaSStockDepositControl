"""Behavioural tests for backend/docker-entrypoint.sh using stub alembic/uvicorn
binaries."""

import os
import subprocess
from pathlib import Path

import pytest

ENTRYPOINT = Path(__file__).resolve().parents[2] / "docker-entrypoint.sh"

STUB = """#!/usr/bin/env bash
echo "{name} $*" >> "$CALLS_LOG"
{extra}
"""


@pytest.fixture
def sandbox(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    def make_stub(name: str, extra: str = "") -> None:
        path = bin_dir / name
        path.write_text(STUB.format(name=name, extra=extra))
        path.chmod(0o755)

    make_stub("alembic")
    make_stub("uvicorn")
    make_stub("custom-cmd")
    return tmp_path, make_stub


def run_entrypoint(sandbox, *args, env=None):
    tmp_path, _ = sandbox
    log = tmp_path / "calls.log"
    full_env = {
        "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}",
        "APP_DIR": str(tmp_path / "app"),
        "CALLS_LOG": str(log),
        **(env or {}),
    }
    result = subprocess.run(
        ["bash", str(ENTRYPOINT), *args],
        env=full_env,
        capture_output=True,
        text=True,
    )
    calls = log.read_text().splitlines() if log.exists() else []
    return result, calls


MIGRATIONS = [
    "alembic -c backend/migrations/alembic.ini upgrade head",
    "alembic -c backend/migrations/alembic_users.ini upgrade head",
    "alembic -c backend/migrations/alembic_analytics.ini upgrade head",
]


def test_serve_forwards_extra_args_to_uvicorn_after_migrations(sandbox):
    result, calls = run_entrypoint(sandbox, "serve", "--reload")

    assert result.returncode == 0
    assert calls[:3] == MIGRATIONS
    assert calls[3].startswith("uvicorn backend.api.main:app")
    assert calls[3].endswith("--no-access-log --reload")


def test_no_argument_behaves_like_serve(sandbox):
    _, calls = run_entrypoint(sandbox)

    assert calls[:3] == MIGRATIONS
    assert calls[3].startswith("uvicorn backend.api.main:app")
    assert "--reload" not in calls[3]


def test_workers_come_from_environment(sandbox):
    _, calls = run_entrypoint(sandbox, "serve", env={"UVICORN_WORKERS": "1"})

    assert "--workers 1" in calls[3]


def test_run_migrations_false_skips_alembic(sandbox):
    _, calls = run_entrypoint(sandbox, "serve", env={"RUN_MIGRATIONS": "false"})

    assert len(calls) == 1
    assert calls[0].startswith("uvicorn ")


def test_articles_switch_off_skips_only_articles_migrations(sandbox):
    _, calls = run_entrypoint(
        sandbox,
        "serve",
        env={
            "RUN_MIGRATIONS": "true",
            "RUN_MIGRATIONS_ARTICLES": "false",
            "RUN_MIGRATIONS_USERS": "true",
            "RUN_MIGRATIONS_ANALYTICS": "true",
        },
    )

    assert calls[:2] == MIGRATIONS[1:]
    assert calls[2].startswith("uvicorn backend.api.main:app")
    assert len(calls) == 3


@pytest.mark.parametrize(
    ("switch", "skipped"),
    [
        ("RUN_MIGRATIONS_ARTICLES", 0),
        ("RUN_MIGRATIONS_USERS", 1),
        ("RUN_MIGRATIONS_ANALYTICS", 2),
    ],
)
def test_each_database_switch_skips_its_own_config(sandbox, switch, skipped):
    _, calls = run_entrypoint(sandbox, "serve", env={switch: "false"})

    expected = [m for i, m in enumerate(MIGRATIONS) if i != skipped]
    assert calls[:2] == expected
    assert calls[2].startswith("uvicorn ")


def test_run_migrations_false_overrides_database_switches(sandbox):
    _, calls = run_entrypoint(
        sandbox,
        "serve",
        env={
            "RUN_MIGRATIONS": "false",
            "RUN_MIGRATIONS_ARTICLES": "true",
            "RUN_MIGRATIONS_USERS": "true",
            "RUN_MIGRATIONS_ANALYTICS": "true",
        },
    )

    assert len(calls) == 1
    assert calls[0].startswith("uvicorn ")


def test_failed_migration_aborts_before_uvicorn(sandbox):
    _, make_stub = sandbox
    make_stub("alembic", "exit 3")

    result, calls = run_entrypoint(sandbox, "serve")

    assert result.returncode != 0
    assert calls == [MIGRATIONS[0]]


def test_other_commands_are_exec_untouched_without_migrations(sandbox):
    result, calls = run_entrypoint(sandbox, "custom-cmd", "--flag", "x")

    assert result.returncode == 0
    assert calls == ["custom-cmd --flag x"]
