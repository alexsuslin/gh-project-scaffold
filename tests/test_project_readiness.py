import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import commit_fixture, git
from test_generator import snapshot

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "github-project-ops/scripts/scaffold.py"


def run(*arguments):
    # -S proves these commands do not depend on Copier/site-packages.
    return subprocess.run(
        [sys.executable, "-S", str(SCRIPT), *map(str, arguments)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "existing project"
    root.mkdir()
    git(root, "init", "-b", "main")
    (root / "application.txt").write_bytes(b"existing user work\r\n")
    return root


def test_doctor_discovers_commands_without_executing_scripts_or_modifying_git(repository):
    (repository / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "echo secret; touch EXECUTED",
                    "build": "arbitrary code",
                }
            }
        )
    )
    (repository / "package-lock.json").write_text("{}")
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)
    result = run("doctor", repository, "--json")
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["schema_version"] == 1
    assert report["stacks"] == ["node"]
    assert report["git"]["dirty"] is True
    assert report["checks_executed"] is False
    assert report["commands"][0]["command"] == "npm run test"
    assert "secret" not in result.stdout
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


def test_doctor_reports_actual_root_and_nested_repository(repository, monkeypatch):
    child = repository / "src"
    child.mkdir()
    report = json.loads(run("doctor", child, "--json").stdout)
    assert Path(report["root"]) == repository.resolve()
    assert "not_git_root" in {f["code"] for f in report["findings"]}
    # Fixtures may live under this repository; stop discovery before that outer root.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(repository.parent.parent))
    report = json.loads(run("doctor", repository.parent, "--json").stdout)
    assert str(repository) in report["git"]["nested_roots"]
    result = run("adopt", child)
    assert result.returncode == 2
    assert not (repository / ".scaffold.json").exists()


def test_doctor_detects_mixed_stack_and_bad_metadata(repository):
    (repository / "pyproject.toml").write_text("[tool.pytest.ini_options]\ntestpaths=['tests']")
    (repository / "package.json").write_text("[]")
    (repository / "App").mkdir()
    (repository / "App/App.csproj").write_text("<Project />")
    report = json.loads(run("doctor", repository, "--json").stdout)
    assert report["stacks"] == ["python", "node", "dotnet"]
    assert report["commands"][0]["command"] == "python -m pytest"
    assert "invalid_node_metadata" in {f["code"] for f in report["findings"]}


def test_doctor_invalid_path_is_machine_readable(tmp_path):
    result = run("doctor", tmp_path / "missing", "--json")
    assert result.returncode == 2
    assert json.loads(result.stdout)["schema_version"] == 1


def test_doctor_and_adopt_work_in_a_linked_worktree(repository, tmp_path):
    git(repository, "add", "application.txt")
    commit_fixture(repository, "Baseline")
    worktree = tmp_path / "linked tree"
    git(repository, "worktree", "add", "-b", "task", str(worktree))
    before = snapshot(repository)
    result = run("adopt", worktree)
    assert result.returncode == 0, result.stderr
    report = json.loads(run("doctor", worktree, "--json").stdout)
    assert Path(report["root"]) == worktree.resolve()
    assert report["git"]["branch"] == "task"
    assert {Path(p) for p in report["git"]["worktrees"]} == {repository, worktree}
    assert snapshot(repository) == before


def test_doctor_disables_git_fsmonitor_hooks(repository):
    hook = repository / ".git/fsmonitor-test"
    hook.write_text("#!/bin/sh\nprintf ran > FS_MONITOR_EXECUTED\n", encoding="utf-8")
    hook.chmod(0o755)
    git(repository, "config", "core.fsmonitor", hook.as_posix())
    result = run("doctor", repository, "--json")
    assert json.loads(result.stdout)["git"]["dirty"] is True
    assert not (repository / "FS_MONITOR_EXECUTED").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction check")
def test_windows_junction_docs_are_rejected(repository, tmp_path):
    outside = tmp_path / "outside-junction"
    outside.mkdir()
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(repository / "docs"), str(outside)],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        pytest.skip("Junction creation unavailable")
    result = run("adopt", repository)
    assert result.returncode == 2
    assert "reparse point" in result.stderr
    assert list(outside.iterdir()) == []
    assert not (repository / "AGENTS.md").exists()


def test_adopt_preview_apply_and_repeat_preserve_dirty_and_ignored_files(repository):
    (repository / ".gitignore").write_text(".env\n")
    (repository / ".env").write_text("private fixture")
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)
    result = run("adopt", repository, "--preview")
    assert result.returncode == 0, result.stderr
    assert "+# Project instructions" in result.stdout
    assert "docs/HANDOFF.md" in result.stdout
    assert snapshot(repository) == before
    result = run("adopt", repository)
    assert result.returncode == 0, result.stderr
    after = snapshot(repository)
    assert all(after[name] == content for name, content in before.items())
    assert set(after) - set(before) == {"AGENTS.md", "docs/HANDOFF.md", ".scaffold.json"}
    manifest = json.loads((repository / ".scaffold.json").read_text())
    assert set(manifest["created_files"]) == {"AGENTS.md", "docs/HANDOFF.md"}
    assert not (repository / ".copier-answers.yml").exists()
    (repository / "AGENTS.md").write_text("Edited by owner")
    (repository / "docs/HANDOFF.md").write_text("Actual task and evidence")
    before_repeat = snapshot(repository)
    result = run("adopt", repository)
    assert result.returncode == 0, result.stderr
    assert snapshot(repository) == before_repeat
    assert (repository / ".git/index").read_bytes() == index


@pytest.mark.parametrize("instructions", ["AGENTS.md", "AGENTS.override.md"])
def test_existing_guidance_and_custom_context_remain_byte_identical(repository, instructions):
    (repository / instructions).write_bytes(b"User-owned instructions\r\n")
    (repository / "CONTEXT.md").write_bytes(b"Existing status\r\n")
    before = snapshot(repository)
    result = run("adopt", repository, "--handoff", "CONTEXT.md")
    assert result.returncode == 0, result.stderr
    assert "Review existing instructions" in result.stdout
    after = snapshot(repository)
    assert all(after[name] == content for name, content in before.items())
    assert set(after) - set(before) == {".scaffold.json"}
    report = json.loads(run("doctor", repository, "--json").stdout)
    assert report["handoff"] == "CONTEXT.md"
    assert "missing_handoff" not in {f["code"] for f in report["findings"]}


@pytest.mark.parametrize(
    "name", ["../outside.md", "/outside.md", "D:/outside.md", "AGENTS.md", ".git/context.md"]
)
def test_unsafe_handoff_is_rejected_without_writes(repository, name):
    before = snapshot(repository)
    result = run("adopt", repository, "--handoff", name)
    assert result.returncode == 2
    assert snapshot(repository) == before


@pytest.mark.parametrize(
    "collision", ["docs", "docs/HANDOFF.md", "AGENTS.md", ".scaffold.json", ".copier-answers.yml"]
)
def test_conflicts_are_rejected_before_any_write(repository, collision):
    target = repository / collision
    target.parent.mkdir(parents=True, exist_ok=True)
    if collision in ("AGENTS.md", "docs/HANDOFF.md"):
        target.mkdir()
    else:
        target.write_text("not a valid adoption baseline")
    before = snapshot(repository)
    for extra in ([], ["--preview"]):
        result = run("adopt", repository, *extra)
        assert result.returncode == 2, result.stdout
        assert snapshot(repository) == before


def test_symlinked_docs_are_not_followed(repository, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        os.symlink(outside, repository / "docs", target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation unavailable")
    result = run("adopt", repository)
    assert result.returncode == 2
    assert not (repository / "AGENTS.md").exists()
    assert list(outside.iterdir()) == []


def test_missing_adopted_file_is_reported_without_silent_recreation(repository):
    assert run("adopt", repository).returncode == 0
    (repository / "AGENTS.md").unlink()
    result = run("doctor", repository, "--json")
    report = json.loads(result.stdout)
    assert "missing_adopted_file" in {f["code"] for f in report["findings"]}
    assert run("adopt", repository).returncode == 0
    assert not (repository / "AGENTS.md").exists()


def test_write_failure_rolls_back_only_new_files(repository, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "readiness", SCRIPT.with_name("project_readiness.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_open = Path.open

    def failing_open(path, *args, **kwargs):
        if path.name == ".scaffold.json" and args == ("xb",):
            raise PermissionError("simulated failure")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)
    before = snapshot(repository)
    with pytest.raises(PermissionError):
        module.write_additions(repository, {"docs/HANDOFF.md": b"new", ".scaffold.json": b"{}"})
    assert snapshot(repository) == before
    assert not (repository / "docs").exists()


def test_custom_handoff_link_and_legacy_guidance_are_preserved(repository):
    (repository / "Current Context.md").write_text("Current project context")
    (repository / "AGENT.md").write_text("Important existing convention")
    result = run("adopt", repository, "--handoff", "Current Context.md")
    assert result.returncode == 0, result.stderr
    agents = (repository / "AGENTS.md").read_text()
    assert "(Current%20Context.md)" in agents
    assert "[AGENT.md](AGENT.md)" in agents
    assert (repository / "AGENT.md").read_text() == "Important existing convention"
