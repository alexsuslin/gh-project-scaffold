import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TEMPLATES = Path(__file__).resolve().parents[1] / "github-project-ops" / "assets" / "templates"


@pytest.mark.parametrize(
    ("tag", "expected_code"), [("v0.1.0", 0), ("v0.2.0", 1), ("v0.1.0-rc1", 1)]
)
def test_release_checks_actual_tag_against_package_metadata(tmp_path, tag, expected_code):
    workflow = yaml.safe_load(
        (TEMPLATES / ".github/workflows/release.yml").read_text(encoding="utf-8")
    )
    check = next(
        step for step in workflow["jobs"]["build"]["steps"] if step.get("shell") == "python"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "example"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, "-c", check["run"]],
        cwd=tmp_path,
        env={**os.environ, "GITHUB_REF_NAME": tag},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected_code, result.stdout + result.stderr
    if expected_code:
        assert tag in result.stderr
        assert "v0.1.0" in result.stderr
