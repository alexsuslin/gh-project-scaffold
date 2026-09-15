import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def git(root, *arguments):
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


def commit_fixture(root, message):
    # Fixture repositories use a synthetic identity, never the user's hardware key.
    git(
        root,
        "-c",
        "user.name=Scaffold test",
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        message,
    )


@pytest.fixture
def template_source(tmp_path):
    source = tmp_path / "template-source"
    source.mkdir()
    if (ROOT / "copier.yml").exists():
        shutil.copy2(ROOT / "copier.yml", source)
    shutil.copytree(
        ROOT / "github-project-ops",
        source / "github-project-ops",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    git(source, "init", "-b", "main")
    git(source, "add", ".")
    commit_fixture(source, "Template v1")
    git(source, "tag", "v1.0.0")
    return source
