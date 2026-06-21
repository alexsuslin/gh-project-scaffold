from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "github-project-ops"
TMP_ROOT = REPO_ROOT / "tmp-test-runs"


def read(relative_path: str) -> str:
    return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")


def read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def make_temp_dir(name: str) -> Path:
    path = TMP_ROOT / name
    if path.exists():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
    path.mkdir(parents=True, exist_ok=False)
    return path


def test_skill_layout_exists():
    expected = [
        SKILL_ROOT / "SKILL.md",
        SKILL_ROOT / "agents" / "openai.yaml",
        SKILL_ROOT / "references" / "repo-standards.md",
        SKILL_ROOT / "references" / "python-defaults.md",
        SKILL_ROOT / "references" / "github-actions.md",
        SKILL_ROOT / "scripts" / "validate_scaffold.py",
        SKILL_ROOT / "assets" / "templates",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    assert not missing, f"Missing expected skill paths: {missing}"


def test_skill_instructions_cover_modes_and_defaults():
    text = read("SKILL.md")
    required = [
        "Bootstrap mode",
        "Audit mode",
        "Release mode",
        "Maintenance mode",
        "Python-first",
        "public",
    ]
    missing = [item for item in required if item not in text]
    assert not missing, f"Missing skill guidance: {missing}"


def test_template_inventory_exists():
    root = SKILL_ROOT / "assets" / "templates"
    expected = [
        root / "README.public.md",
        root / "README.private.md",
        root / "AGENTS.md",
        root / "CONTRIBUTING.md",
        root / "SECURITY.md",
        root / "CHANGELOG.md",
        root / "pyproject.toml",
        root / ".github" / "workflows" / "ci.yml",
        root / ".github" / "workflows" / "release.yml",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    assert not missing, f"Missing templates: {missing}"


def test_readme_uses_portable_paths():
    text = read_repo_file("README.md")
    assert "C:\\Users\\" not in text
    assert "$env:USERPROFILE" in text


def test_repo_ignores_test_artifacts():
    text = read_repo_file(".gitignore")
    assert "tmp-test-runs/" in text


def test_repo_validator_accepts_public_sample():
    tmp_path = make_temp_dir("public-sample")
    (tmp_path / "README.md").write_text("# Sample\n", encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'sample-project'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SKILL_ROOT / "scripts" / "validate_scaffold.py"),
            "--public",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Scaffold looks complete." in result.stdout
