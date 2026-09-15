import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml
from conftest import commit_fixture, git

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "github-project-ops/scripts/scaffold.py"


def scaffold(*arguments, temp):
    return subprocess.run(
        [sys.executable, str(GENERATOR), *map(str, arguments)],
        env={**os.environ, "TMP": str(temp), "TEMP": str(temp)},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def create(target, source, temp, *extra):
    return scaffold(
        "create",
        target,
        "--name",
        "weather-kit",
        "--owner",
        "example",
        "--source",
        source,
        "--ref",
        "v1.0.0",
        *extra,
        temp=temp,
    )


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def test_preview_shows_diff_without_creating_destination(template_source, tmp_path):
    target = tmp_path / "new parent" / "weather"
    result = create(target, template_source, tmp_path, "--preview")
    assert result.returncode == 0, result.stderr
    assert not target.parent.exists()
    assert "README.md" in result.stdout and "+# weather-kit" in result.stdout
    assert "weather_kit" in result.stdout


@pytest.mark.parametrize("visibility", ["public", "private"])
def test_create_renders_names_metadata_and_answers(template_source, tmp_path, visibility):
    target = tmp_path / "weather"
    result = create(target, template_source, tmp_path, "--visibility", visibility)
    assert result.returncode == 0, result.stderr
    metadata = tomllib.loads((target / "pyproject.toml").read_text())
    assert metadata["project"]["name"] == "weather-kit"
    assert metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/weather_kit"]
    assert (target / "src/weather_kit/__init__.py").is_file()
    answers = yaml.safe_load((target / ".copier-answers.yml").read_text())
    assert answers["_commit"] == "v1.0.0"
    assert answers["project_name"] == "weather-kit"
    assert (target / "CONTRIBUTING.md").exists() == (visibility == "public")
    assert not (target / "README.public.md").exists()
    assert "THE SOFTWARE IS PROVIDED" in (target / "LICENSE").read_text()


@pytest.mark.parametrize("name", ["../escape", "bad/name", "bad name", "-leading"])
def test_invalid_name_never_creates_files(template_source, tmp_path, name):
    target = tmp_path / "weather"
    result = scaffold(
        "create",
        target,
        "--name",
        name,
        "--owner",
        "example",
        "--source",
        template_source,
        temp=tmp_path,
    )
    assert result.returncode != 0
    assert not target.exists()


def test_existing_files_are_never_overwritten(template_source, tmp_path):
    target = tmp_path / "weather"
    target.mkdir()
    (target / "README.md").write_text("User work")
    before = snapshot(target)
    result = create(target, template_source, tmp_path)
    assert result.returncode != 0
    assert snapshot(target) == before


def prepared_project(source, tmp_path):
    target = tmp_path / "weather"
    result = create(target, source, tmp_path)
    assert result.returncode == 0, result.stderr
    git(target, "init", "-b", "main")
    git(target, "add", ".")
    commit_fixture(target, "Initial project")
    return target


def bump_template(source):
    asset = source / "github-project-ops/assets/templates/AGENTS.md"
    asset.write_text(asset.read_text() + "\nNew upstream guidance.\n")
    git(source, "add", ".")
    commit_fixture(source, "Template v2")
    git(source, "tag", "v2.0.0")


def test_update_preview_preserves_files_and_git_index(template_source, tmp_path):
    target = prepared_project(template_source, tmp_path)
    bump_template(template_source)
    before = snapshot(target)
    head = git(target, "rev-parse", "HEAD")
    result = scaffold("update", target, "--ref", "v2.0.0", "--preview", temp=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "+New upstream guidance." in result.stdout
    assert snapshot(target) == before
    assert git(target, "rev-parse", "HEAD") == head
    assert git(target, "status", "--porcelain") == ""


def test_update_preserves_user_changes(template_source, tmp_path):
    target = prepared_project(template_source, tmp_path)
    (target / "application.txt").write_text("User-owned application data")
    with (target / "README.md").open("a") as stream:
        stream.write("\nUser documentation\n")
    git(target, "add", ".")
    commit_fixture(target, "User work")
    bump_template(template_source)
    result = scaffold("update", target, "--ref", "v2.0.0", temp=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "New upstream guidance." in (target / "AGENTS.md").read_text()
    assert "User documentation" in (target / "README.md").read_text()
    assert (target / "application.txt").read_text() == "User-owned application data"
    answers = yaml.safe_load((target / ".copier-answers.yml").read_text())
    assert answers["_commit"] == "v2.0.0"


def test_dirty_project_is_rejected_without_changes(template_source, tmp_path):
    target = prepared_project(template_source, tmp_path)
    (target / "README.md").write_text("Uncommitted user work")
    before = snapshot(target)
    result = scaffold("update", target, "--preview", temp=tmp_path)
    assert result.returncode != 0
    assert snapshot(target) == before
    assert "clean" in result.stderr.lower()


def test_conflicting_update_reports_conflict_without_writing(template_source, tmp_path):
    target = prepared_project(template_source, tmp_path)
    (target / "AGENTS.md").write_text("User replaced this guidance\n")
    git(target, "add", ".")
    commit_fixture(target, "User guidance")
    (template_source / "github-project-ops/assets/templates/AGENTS.md").write_text(
        "Upstream replaced this guidance\n"
    )
    git(template_source, "add", ".")
    commit_fixture(template_source, "Conflicting template")
    git(template_source, "tag", "v2.0.0")
    before = snapshot(target)
    result = scaffold("update", target, "--ref", "v2.0.0", temp=tmp_path)
    assert result.returncode == 3, result.stdout + result.stderr
    assert "AGENTS.md" in result.stdout + result.stderr
    assert snapshot(target) == before
    assert git(target, "status", "--porcelain") == ""


def test_unicode_description_produces_valid_toml(template_source, tmp_path):
    target = tmp_path / "weather"
    description = 'Weather \U0001f326 "forecast"\nSecond line'
    result = create(target, template_source, tmp_path, "--description", description)
    assert result.returncode == 0, result.stderr
    metadata = tomllib.loads((target / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["description"] == description


@pytest.mark.parametrize("ignore_location", [".gitignore", ".git/info/exclude"])
def test_update_preserves_ignored_local_files(template_source, tmp_path, ignore_location):
    target = prepared_project(template_source, tmp_path)
    ignore = target / ignore_location
    with ignore.open("a") as stream:
        stream.write("\nlocal.ini\n")
    if ignore_location == ".gitignore":
        git(target, "add", ".gitignore")
        commit_fixture(target, "Ignore local config")
    (target / "local.ini").write_text("private local settings")
    (template_source / "github-project-ops/assets/templates/local.ini").write_text(
        "upstream settings"
    )
    git(template_source, "add", ".")
    commit_fixture(template_source, "Add local.ini")
    git(template_source, "tag", "v2.0.0")
    before = snapshot(target)
    result = scaffold("update", target, "--ref", "v2.0.0", temp=tmp_path)
    assert result.returncode != 0
    assert snapshot(target) == before
    assert "local.ini" in result.stderr


@pytest.mark.parametrize("change", ["delete", "rename"])
def test_update_applies_template_file_removals(template_source, tmp_path, change):
    target = prepared_project(template_source, tmp_path)
    asset = template_source / "github-project-ops/assets/templates/AGENTS.md"
    if change == "rename":
        asset.rename(asset.with_name("RULES.md"))
    else:
        asset.unlink()
    git(template_source, "add", ".")
    commit_fixture(template_source, "Remove old template path")
    git(template_source, "tag", "v2.0.0")
    result = scaffold("update", target, "--ref", "v2.0.0", temp=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (target / "AGENTS.md").exists()
    assert (target / "RULES.md").exists() == (change == "rename")


def test_no_license_option_omits_license_file(template_source, tmp_path):
    target = tmp_path / "weather"
    result = create(target, template_source, tmp_path, "--license", "none")
    assert result.returncode == 0, result.stderr
    assert not (target / "LICENSE").exists()
    assert "license" not in tomllib.loads((target / "pyproject.toml").read_text())["project"]


def test_preview_outputs_unicode_as_utf8(template_source, tmp_path):
    target = tmp_path / "weather"
    result = create(
        target, template_source, tmp_path, "--description", "Weather \U0001f326", "--preview"
    )
    assert result.returncode == 0, result.stderr
    assert "Weather \U0001f326" in result.stdout
    assert not target.exists()
