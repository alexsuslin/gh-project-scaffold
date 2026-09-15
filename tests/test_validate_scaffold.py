import json
import subprocess
import sys
from pathlib import Path

import pytest

VALIDATOR = (
    Path(__file__).resolve().parents[1] / "github-project-ops" / "scripts" / "validate_scaffold.py"
)


@pytest.fixture
def scaffold(tmp_path):
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "example"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci\n", encoding="utf-8")
    return tmp_path


def validate(root, *options):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(root), *options],
        capture_output=True,
        text=True,
        check=False,
    )


def test_json_success_is_machine_readable(scaffold):
    result = validate(scaffold, "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["stack"] == "python"
    assert report["missing"] == []
    assert report["errors"] == []


def test_public_mode_lists_missing_community_docs(scaffold):
    result = validate(scaffold, "--public", "--json")
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert report["missing"] == ["CONTRIBUTING.md", "SECURITY.md"]


def test_directory_cannot_stand_in_for_a_required_file(scaffold):
    readme = scaffold / "README.md"
    readme.unlink()
    readme.mkdir()
    result = validate(scaffold)
    assert result.returncode == 1
    assert "README.md" in result.stdout


@pytest.mark.parametrize("content", ["", "  \n\t"])
def test_empty_required_file_is_rejected(scaffold, content):
    (scaffold / "README.md").write_text(content, encoding="utf-8")
    result = validate(scaffold)
    assert result.returncode == 1
    assert "README.md" in result.stdout


def test_alternate_workflow_extension_is_accepted(scaffold):
    workflows = scaffold / ".github" / "workflows"
    (workflows / "ci.yml").rename(workflows / "ci.yaml")
    assert validate(scaffold).returncode == 0


def test_generic_mode_does_not_require_python_metadata(scaffold):
    (scaffold / "pyproject.toml").unlink()
    result = validate(scaffold, "--stack", "generic", "--json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["stack"] == "generic"
    assert validate(scaffold).returncode == 1


def test_generic_mode_ignores_unrelated_python_metadata(scaffold):
    (scaffold / "pyproject.toml").write_text("[invalid", encoding="utf-8")
    assert validate(scaffold, "--stack", "generic").returncode == 0


def test_invalid_toml_produces_actionable_error(scaffold):
    (scaffold / "pyproject.toml").write_text("[project", encoding="utf-8")
    result = validate(scaffold, "--json")
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["missing"] == []
    assert "pyproject.toml" in report["errors"][0]


def test_invalid_utf8_produces_report_instead_of_traceback(scaffold):
    (scaffold / "README.md").write_bytes(b"\xff")
    result = validate(scaffold, "--json")
    assert result.returncode == 1
    assert "README.md" in json.loads(result.stdout)["errors"][0]
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("is_file", [False, True])
def test_invalid_root_is_usage_error(tmp_path, is_file):
    root = tmp_path / "not-a-repository"
    if is_file:
        root.write_text("file", encoding="utf-8")
    result = validate(root, "--json")
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert report["errors"]
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("blocked_name", ["README.md", "ci.yml", "ci.yaml"])
def test_permission_error_during_file_check_still_emits_json(
    scaffold, monkeypatch, capsys, blocked_name
):
    import runpy

    if blocked_name == "ci.yaml":
        workflows = scaffold / ".github/workflows"
        (workflows / "ci.yml").rename(workflows / "ci.yaml")
    command = runpy.run_path(str(VALIDATOR))["main"]
    original_is_file = Path.is_file

    def denied_metadata(path):
        if path.name == blocked_name:
            raise PermissionError(f"Cannot access {path}")
        return original_is_file(path)

    # Metadata errors are platform-dependent; simulate only the filesystem boundary.
    monkeypatch.setattr(Path, "is_file", denied_metadata)
    monkeypatch.setattr(sys, "argv", [str(VALIDATOR), str(scaffold), "--json"])
    assert command() == 1
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is False
    assert blocked_name in report["errors"][0]
