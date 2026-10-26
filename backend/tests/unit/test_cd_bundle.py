"""
The CD workflow ships a fixed file bundle to target hosts (DEPLOY_FILES in
.github/workflows/cd.yml). Anything deploy.sh can reference must be in it.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CD_WORKFLOW = ROOT / ".github" / "workflows" / "cd.yml"


def deploy_files() -> list[str]:
    match = re.search(
        r"^\s*DEPLOY_FILES: >-\n((?:\s{4,}\S.*\n)+)", CD_WORKFLOW.read_text(), re.M
    )
    assert match, "DEPLOY_FILES block not found in cd.yml"
    return match.group(1).split()


def test_bundle_ships_every_root_compose_file():
    shipped = set(deploy_files())
    compose_files = {p.name for p in ROOT.glob("docker-compose*.yml")}
    # The dev override is for local hot reload, never deployed.
    compose_files.discard("docker-compose.dev.yml")

    assert compose_files <= shipped, compose_files - shipped


def test_every_bundled_file_exists():
    missing = [f for f in deploy_files() if not (ROOT / f).is_file()]
    assert not missing, missing
