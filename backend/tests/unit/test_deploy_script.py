"""
Behavioural tests for scripts/devops/deploy.sh using stub docker/curl/sleep binaries.
"""

import gzip
import os
import stat
import subprocess
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[3] / "scripts" / "devops" / "deploy.sh"

DOCKER_STUB = """#!/usr/bin/env bash
echo "docker $* [IMAGE_TAG=${IMAGE_TAG:-}]" >> "$CALLS_LOG"
case "$*" in
  *" ps "*) echo "${STUB_RUNNING:-}" ;;
  *mariadb-dump*)
    echo "-- dump"
    exit "${STUB_DUMP_RC:-0}"
    ;;
esac
"""

# Healthy unless the deployed tag is "bad" (read from the .env under test).
CURL_STUB = """#!/usr/bin/env bash
echo "curl $*" >> "$CALLS_LOG"
if grep -q '^IMAGE_TAG=bad$' "$DEPLOY_ROOT/.env"; then
  exit 22
fi
echo '{"status":"healthy"}'
"""

SLEEP_STUB = """#!/usr/bin/env bash
echo "sleep $*" >> "$CALLS_LOG"
"""

EXTERNAL_DUMP_STUB = """#!/usr/bin/env bash
echo "mariadb-dump $*" >> "$CALLS_LOG"
echo "-- external"
"""


@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / ".env").write_text("IMAGE_TAG=v1\nDB_PASSWORD=s3cret\n")
    (root / "docker-compose.yml").write_text("services: {}\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    def make_stub(name: str, body: str) -> None:
        path = bin_dir / name
        path.write_text(body)
        path.chmod(0o755)

    make_stub("docker", DOCKER_STUB)
    make_stub("curl", CURL_STUB)
    make_stub("sleep", SLEEP_STUB)
    return tmp_path, root, make_stub


def run_deploy(sandbox, *args, env=None):
    tmp_path, root, _ = sandbox
    log = tmp_path / "calls.log"
    full_env = {
        "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}",
        "DEPLOY_ROOT": str(root),
        "CALLS_LOG": str(log),
        **(env or {}),
    }
    result = subprocess.run(
        ["bash", str(DEPLOY), *args],
        env=full_env,
        capture_output=True,
        text=True,
        check=False,
    )
    calls = log.read_text().splitlines() if log.exists() else []
    return result, calls


def curl_calls(calls):
    return [c for c in calls if c.startswith("curl ")]


def up_calls(calls):
    return [c for c in calls if " up -d" in c]


def test_update_records_previous_tag_and_switches_env(sandbox):
    _, root, _ = sandbox

    result, calls = run_deploy(sandbox, "update", "v2")

    assert result.returncode == 0, result.stderr
    assert (root / ".previous_tag").read_text().strip() == "v1"
    assert "IMAGE_TAG=v2\n" in (root / ".env").read_text()
    assert "IMAGE_TAG=v1" not in (root / ".env").read_text()
    pulls = [c for c in calls if " pull backend web" in c]
    assert len(pulls) == 1 and pulls[0].endswith("[IMAGE_TAG=v2]")


def test_update_to_unhealthy_tag_rolls_back_to_previous_tag(sandbox):
    _, root, _ = sandbox

    result, calls = run_deploy(sandbox, "update", "bad")

    assert result.returncode != 0
    assert "IMAGE_TAG=v1\n" in (root / ".env").read_text()
    assert (root / ".previous_tag").read_text().strip() == "v1"
    # new tag + rollback to the previous tag
    assert len(up_calls(calls)) == 2
    # default window is 60s: probes at 0, 5, ..., 60 (13) + 1 after rollback
    assert len(curl_calls(calls)) == 13 + 1


def test_health_timeout_is_configurable(sandbox):
    _, calls = run_deploy(sandbox, "update", "bad", env={"HEALTH_TIMEOUT": "10"})

    # probes at 0, 5, 10 (3) + 1 after rollback
    assert len(curl_calls(calls)) == 3 + 1


def test_update_to_current_tag_keeps_rollback_target(sandbox):
    _, root, _ = sandbox
    (root / ".previous_tag").write_text("v0\n")

    result, _ = run_deploy(sandbox, "update", "v1")

    assert result.returncode == 0, result.stderr
    assert (root / ".previous_tag").read_text().strip() == "v0"


def test_update_rejects_unsafe_tag_without_touching_anything(sandbox):
    _, root, _ = sandbox
    before = (root / ".env").read_text()

    result, calls = run_deploy(sandbox, "update", "v2|x")

    assert result.returncode != 0
    assert (root / ".env").read_text() == before
    assert not (root / ".previous_tag").exists()
    assert not [c for c in calls if " pull" in c or " up -d" in c]


def test_rollback_restores_previous_tag_and_verifies_health(sandbox):
    _, root, _ = sandbox
    (root / ".previous_tag").write_text("v0\n")

    result, calls = run_deploy(sandbox, "rollback")

    assert result.returncode == 0, result.stderr
    assert "IMAGE_TAG=v0\n" in (root / ".env").read_text()
    assert len(up_calls(calls)) == 1
    assert len(curl_calls(calls)) == 1


def test_rollback_without_previous_tag_fails_and_changes_nothing(sandbox):
    _, root, _ = sandbox
    before = (root / ".env").read_text()

    result, calls = run_deploy(sandbox, "rollback")

    assert result.returncode != 0
    assert (root / ".env").read_text() == before
    assert not up_calls(calls)


def test_rollback_fails_when_previous_tag_is_also_unhealthy(sandbox):
    _, root, _ = sandbox
    (root / ".previous_tag").write_text("bad\n")

    result, _ = run_deploy(sandbox, "rollback")

    assert result.returncode != 0


def test_pull_pulls_images_without_touching_env(sandbox):
    _, root, _ = sandbox
    before = (root / ".env").read_text()

    result, calls = run_deploy(sandbox, "pull")

    assert result.returncode == 0, result.stderr
    assert [c for c in calls if " pull backend web" in c]
    assert (root / ".env").read_text() == before
    assert not up_calls(calls)


def test_backup_from_bundled_mariadb_writes_private_gzip(sandbox):
    _, root, _ = sandbox

    result, calls = run_deploy(sandbox, "backup", env={"STUB_RUNNING": "mariadb"})

    assert result.returncode == 0, result.stderr
    archives = list((root / "backups").glob("backup_*.sql.gz"))
    assert len(archives) == 1
    assert stat.S_IMODE(archives[0].stat().st_mode) == 0o600
    assert "-- dump" in gzip.decompress(archives[0].read_bytes()).decode()
    dump = [c for c in calls if "mariadb-dump" in c]
    assert "db_articles db_users db_analytics" in dump[0]


def test_backup_from_external_database_keeps_password_off_argv(sandbox):
    _, root, make_stub = sandbox
    make_stub("mariadb-dump", EXTERNAL_DUMP_STUB)

    result, calls = run_deploy(sandbox, "backup")

    assert result.returncode == 0, result.stderr
    archives = list((root / "backups").glob("backup_*.sql.gz"))
    assert len(archives) == 1
    assert "-- external" in gzip.decompress(archives[0].read_bytes()).decode()
    assert not [c for c in calls if "s3cret" in c]


def test_failed_dump_leaves_no_archive(sandbox):
    _, root, _ = sandbox

    result, _ = run_deploy(
        sandbox, "backup", env={"STUB_RUNNING": "mariadb", "STUB_DUMP_RC": "2"}
    )

    assert result.returncode != 0
    assert list((root / "backups").iterdir()) == []


def test_help_lists_lifecycle_commands(sandbox):
    result, _ = run_deploy(sandbox, "help")

    assert result.returncode == 0
    for command in ("pull", "update", "rollback", "backup"):
        assert command in result.stdout


def pull_calls(calls):
    return [c for c in calls if " pull backend web" in c]


def test_compose_uses_only_base_file_without_compose_file_in_env(sandbox):
    _, root, _ = sandbox

    result, calls = run_deploy(sandbox, "pull")

    assert result.returncode == 0, result.stderr
    [pull] = pull_calls(calls)
    assert f"-f {root}/docker-compose.yml --env-file" in pull


def test_compose_file_in_env_adds_public_override(sandbox):
    _, root, _ = sandbox
    (root / "docker-compose.public.yml").write_text("services: {}\n")
    with (root / ".env").open("a") as env:
        env.write("COMPOSE_FILE=docker-compose.yml:docker-compose.public.yml\n")

    result, calls = run_deploy(sandbox, "pull")

    assert result.returncode == 0, result.stderr
    [pull] = pull_calls(calls)
    assert (
        f"-f {root}/docker-compose.yml -f {root}/docker-compose.public.yml --env-file"
        in pull
    )


def test_missing_compose_file_from_env_fails_before_compose_runs(sandbox):
    _, root, _ = sandbox
    with (root / ".env").open("a") as env:
        env.write("COMPOSE_FILE=docker-compose.yml:docker-compose.public.yml\n")

    result, calls = run_deploy(sandbox, "pull")

    assert result.returncode != 0
    assert "docker-compose.public.yml" in result.stderr
    assert not pull_calls(calls)
