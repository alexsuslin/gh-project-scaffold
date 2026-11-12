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
PAPER_LAB_UNITTEST = r"& '.\.venv-paper\Scripts\python.exe' -m unittest discover -s tests -q"
PESTER_README_CHECK = r"""Import-Module Pester -RequiredVersion 3.4.0
$results = foreach ($suite in Get-ChildItem -LiteralPath .\vault\_system\tests -Filter '*.Tests.ps1') {
    Invoke-Pester -Script $suite.FullName -PassThru
}
$results | Select-Object PassedCount, FailedCount
if (($results | Measure-Object FailedCount -Sum).Sum -gt 0) { throw 'Tests failed' }"""


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


@pytest.mark.parametrize(
    "instructions",
    [
        "~~~powershell\nnpm ci --ignore-scripts\nnpm run check\nnpm test\n~~~\n",
        "Install with `npm ci --ignore-scripts` before running checks.\n",
    ],
    ids=["jev-advisor-fenced-setup", "inline-setup"],
)
def test_doctor_prefers_documented_npm_ci_without_running_it(repository, instructions):
    (repository / "package.json").write_text('{"scripts":{"test":"node --test"}}')
    (repository / "package-lock.json").write_text("{}")
    (repository / "README.md").write_text(f"# Fixture\n\n{instructions}", encoding="utf-8")
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert [item for item in report["commands"] if item["name"] == "bootstrap"] == [
        {
            "name": "bootstrap",
            "command": "npm ci --ignore-scripts",
            "source": "README.md",
            "verified": False,
        }
    ]
    assert report["checks_executed"] is False
    preview = run("adopt", repository, "--preview")
    assert preview.returncode == 0, preview.stderr
    assert "bootstrap: `npm ci --ignore-scripts`" in preview.stdout
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


@pytest.mark.parametrize(
    "instructions",
    [
        None,
        "Run npm ci --ignore-scripts only if needed.\n",
        "`npm ci --ignore-scripts=false`\n",
        "npm ci --ignore-scripts && echo private-command\n",
    ],
    ids=["missing-readme", "prose", "different-option", "chained-command"],
)
def test_doctor_keeps_npm_ci_without_an_exact_documented_command(repository, instructions):
    (repository / "package.json").write_text("{}")
    (repository / "package-lock.json").write_text("{}")
    if instructions is not None:
        (repository / "README.md").write_text(instructions, encoding="utf-8")

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["commands"] == [
        {"name": "bootstrap", "command": "npm ci", "source": "package-lock.json", "verified": False}
    ]
    assert "private-command" not in result.stdout


@pytest.mark.parametrize(
    "instructions",
    [
        (
            "```sh\nnpm test\n"
            "npm run build        # Build the static site\n"
            "npm run test:browser # Check the built site\n```\n"
        ),
        "Run `npm run build && npm run test:browser` for browser checks.\n",
    ],
    ids=["commented-command-list", "inline-chain"],
)
def test_doctor_suggests_documented_build_before_browser_tests(repository, instructions):
    (repository / "package.json").write_text(
        '{"scripts":{"build":"node build.mjs","test:browser":"playwright test"}}'
    )
    (repository / "package-lock.json").write_text("{}")
    (repository / "README.md").write_text(instructions, encoding="utf-8")
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["commands"] == [
        {
            "name": "build",
            "command": "npm run build",
            "source": "package.json scripts.build",
            "verified": False,
        },
        {
            "name": "test:browser",
            "command": "npm run build && npm run test:browser",
            "source": "README.md",
            "verified": False,
        },
        {
            "name": "bootstrap",
            "command": "npm ci",
            "source": "package-lock.json",
            "verified": False,
        },
    ]
    assert report["checks_executed"] is False
    preview = run("adopt", repository, "--preview")
    assert preview.returncode == 0, preview.stderr
    assert "test:browser: `npm run build && npm run test:browser`" in preview.stdout
    assert snapshot(repository) == before


@pytest.mark.parametrize(
    ("lockfile", "build_script", "instructions", "expected"),
    [
        pytest.param("package-lock.json", True, "", "npm", id="no-instructions"),
        pytest.param(
            "package-lock.json",
            True,
            "npm run test:browser\nnpm run build\n",
            "npm",
            id="reverse-order",
        ),
        pytest.param(
            "package-lock.json",
            True,
            "npm run build -- --mode=development\nnpm run test:browser\n",
            "npm",
            id="build-with-arguments",
        ),
        pytest.param(
            "package-lock.json",
            False,
            "npm run build\nnpm run test:browser\n",
            "npm",
            id="missing-build-script",
        ),
        pytest.param(
            "pnpm-lock.yaml",
            True,
            "npm run build\nnpm run test:browser\n",
            "pnpm",
            id="different-package-manager",
        ),
    ],
)
def test_doctor_keeps_browser_test_candidate_without_npm_build_order(
    repository, lockfile, build_script, instructions, expected
):
    scripts = {"test:browser": "playwright test"}
    if build_script:
        scripts["build"] = "node build.mjs"
    (repository / "package.json").write_text(json.dumps({"scripts": scripts}))
    (repository / lockfile).write_text("{}")
    (repository / "README.md").write_text(instructions, encoding="utf-8")

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert [item for item in report["commands"] if item["name"] == "test:browser"] == [
        {
            "name": "test:browser",
            "command": f"{expected} run test:browser",
            "source": "package.json scripts.test:browser",
            "verified": False,
        }
    ]


@pytest.mark.parametrize(
    ("readme", "rule"),
    [
        ("~~~sh\nmake test\nmake check\n~~~\n", "check:"),
        ("Run `make check` from the repository root.\n", "lint check:"),
        ("make check # Run all local checks\n", "check::"),
    ],
    ids=["fenced-command", "inline-command-and-multiple-targets", "comment-and-double-colon"],
)
def test_doctor_suggests_documented_make_check_without_running_it(repository, readme, rule):
    (repository / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    (repository / "README.md").write_text(readme)
    (repository / "Makefile").write_text(f".PHONY: check\n{rule}\n\t@echo private-fixture\n")
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert [item["command"] for item in report["commands"]] == ["python -m pytest", "make check"]
    assert report["commands"][-1] == {
        "name": "check",
        "command": "make check",
        "source": "README.md and Makefile",
        "verified": False,
    }
    assert report["checks_executed"] is False
    assert "private-fixture" not in result.stdout
    preview = run("adopt", repository, "--preview")
    assert preview.returncode == 0, preview.stderr
    assert "check: `make check`" in preview.stdout
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


@pytest.mark.parametrize(
    ("readme", "makefile"),
    [
        pytest.param(None, "check:\n", id="missing-readme"),
        pytest.param("make check\n", None, id="missing-makefile"),
        pytest.param("make check\n", ".PHONY: check\nall: check\n", id="prerequisite-only"),
        pytest.param("make check\n", "# check:\ncheck-all:\n", id="no-exact-target"),
        pytest.param("make check\n", "check ::= value\n", id="make-variable"),
        pytest.param("make check\n", "other:\n\tcheck:\n", id="recipe-line"),
        pytest.param("make check && echo private-fixture\n", "check:\n", id="compound-command"),
    ],
)
def test_doctor_requires_readme_and_makefile_for_make_check(repository, readme, makefile):
    if readme is not None:
        (repository / "README.md").write_text(readme)
    if makefile is not None:
        (repository / "Makefile").write_text(makefile)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["commands"] == []
    assert "commands_unknown" in {item["code"] for item in report["findings"]}


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


def test_doctor_reports_kidpic_build_and_executable_tests(repository):
    (repository / "build-web.ps1").write_text("'ran' | Set-Content EXECUTED\n")
    (repository / "KidPic.Tests").mkdir()
    (repository / "KidPic.Tests/KidPic.Tests.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
        "<TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>"
    )
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr  # Fixture has no commit, guidance or handoff.
    report = json.loads(result.stdout)
    assert report["stacks"] == ["dotnet"]
    assert report["commands"] == [
        {
            "name": "build",
            "command": "pwsh -File ./build-web.ps1",
            "source": "build-web.ps1",
            "verified": False,
        },
        {
            "name": "test",
            "command": "dotnet run --project ./KidPic.Tests/KidPic.Tests.csproj",
            "source": "KidPic.Tests/KidPic.Tests.csproj [OutputType=Exe]",
            "verified": False,
        },
    ]
    assert "commands_unknown" not in {item["code"] for item in report["findings"]}
    assert report["checks_executed"] is False
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


def test_doctor_does_not_suggest_running_ambiguous_dotnet_projects(repository):
    (repository / "build-web.ps1").mkdir()
    executable = "<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>"
    projects = {
        "KidPic.Web.csproj": executable,
        "Unsafe&Name.Tests.csproj": executable,
        "Library.Tests.csproj": executable.replace("Exe", "Library"),
        "Conditional.Tests.csproj": executable.replace(
            "<PropertyGroup>", '<PropertyGroup Condition="$(Configuration) == Release">'
        ),
        "Broken.Tests.csproj": "<Project><PropertyGroup><OutputType>Exe</OutputType>",
    }
    for name, contents in projects.items():
        (repository / name).write_text(contents)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["stacks"] == ["dotnet"]
    assert report["commands"] == []
    assert "commands_unknown" in {item["code"] for item in report["findings"]}


@pytest.mark.parametrize(
    ("readme", "expected", "source"),
    [
        pytest.param(
            "## Development\n\n- `python312 -m mypy src`\n",
            "python312 -m mypy src",
            "README.md",
            id="teo-tales-readme",
        ),
        pytest.param(
            "```powershell\npython312 -m mypy src\n```\n",
            "python312 -m mypy src",
            "README.md",
            id="standalone-command",
        ),
        pytest.param(
            "`python312 -m mypy src/tests`\npython312 -m mypy src && echo private-command\n",
            "python -m mypy .",
            "pyproject.toml [tool.mypy]",
            id="nonmatching-commands",
        ),
    ],
)
def test_doctor_prefers_documented_mypy_command(repository, readme, expected, source):
    (repository / "pyproject.toml").write_text(
        '[tool.mypy]\npython_version = "3.12"\nstrict = true\nmypy_path = ["src"]\n',
        encoding="utf-8",
    )
    (repository / "README.md").write_text(readme, encoding="utf-8")
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["commands"] == [
        {"name": "mypy", "command": expected, "source": source, "verified": False}
    ]
    assert report["checks_executed"] is False
    assert "private-command" not in result.stdout
    preview = run("adopt", repository, "--preview")
    assert preview.returncode == 0, preview.stderr
    assert f"mypy: `{expected}`" in preview.stdout
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


@pytest.mark.parametrize(
    ("tool", "configuration", "locked", "expected"),
    [
        pytest.param(
            "mypy",
            'python_version = "3.12"\nstrict = true\npackages = ["notion_cli"]\n',
            False,
            "python -m mypy",
            id="notion-cli-mypy-packages",
        ),
        pytest.param(
            "pyright",
            'pythonVersion = "3.13"\ntypeCheckingMode = "strict"\ninclude = ["src", "tests"]\n',
            True,
            "uv run --locked pyright",
            id="busybar-ai-progress-pyright-include",
        ),
        pytest.param(
            "mypy",
            "strict = true\nfiles = []\n",
            True,
            "uv run --locked mypy .",
            id="mypy-without-targets",
        ),
    ],
)
def test_doctor_reports_python_type_check_candidates(
    repository, tool, configuration, locked, expected
):
    (repository / "pyproject.toml").write_text(f"[tool.{tool}]\n{configuration}", encoding="utf-8")
    if locked:
        (repository / "uv.lock").touch()
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr  # Fixture has no commit, guidance, or handoff.
    report = json.loads(result.stdout)
    assert report["stacks"] == ["python"]
    assert [item for item in report["commands"] if item["name"] == tool] == [
        {
            "name": tool,
            "command": expected,
            "source": f"pyproject.toml [tool.{tool}]",
            "verified": False,
        }
    ]
    assert "commands_unknown" not in {item["code"] for item in report["findings"]}
    assert report["checks_executed"] is False
    assert snapshot(repository) == before


@pytest.mark.parametrize("marker", ["project.godot", "game/project.godot"])
def test_doctor_reports_godot_project_check_without_running_it(repository, marker):
    project_file = repository / marker
    project_file.parent.mkdir(exist_ok=True)
    project_file.write_text('config_version=5\n[application]\nconfig/name="Fixture"\n')
    (repository / "scripts").mkdir()
    (repository / "scripts/check.ps1").write_text("'ran' | Set-Content EXECUTED\n")
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["stacks"] == ["godot"]
    assert report["commands"] == [
        {
            "name": "check",
            "command": "pwsh -File ./scripts/check.ps1",
            "source": "scripts/check.ps1",
            "verified": False,
        }
    ]
    assert "commands_unknown" not in {item["code"] for item in report["findings"]}
    assert report["checks_executed"] is False
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


@pytest.mark.parametrize("has_godot_marker", [False, True])
def test_doctor_requires_godot_marker_and_regular_check_script(repository, has_godot_marker):
    (repository / "scripts").mkdir()
    check = repository / "scripts/check.ps1"
    if has_godot_marker:
        (repository / "project.godot").touch()
        check.mkdir()
    else:
        check.touch()

    report = json.loads(run("doctor", repository, "--json").stdout)
    assert report["commands"] == []
    assert "commands_unknown" in {item["code"] for item in report["findings"]}


def test_doctor_reports_documented_paper_lab_check(repository):
    (repository / "pyproject.toml").write_text('[project]\nname = "paper-lab-fixture"\n')
    setup = "$env:PYTHONPATH = 'src'"
    (repository / "README.md").write_text(
        f"# Paper Lab fixture\n\n```powershell\n{setup}\n{PAPER_LAB_UNITTEST}\n"
        "# unrelated command with private-fixture arguments\n```\n",
        encoding="utf-8",
    )
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    expected = f"{setup}; {PAPER_LAB_UNITTEST}"
    assert report["commands"] == [
        {"name": "test", "command": expected, "source": "README.md", "verified": False}
    ]
    assert "commands_unknown" not in {item["code"] for item in report["findings"]}
    assert report["checks_executed"] is False
    assert "private-fixture" not in result.stdout
    preview = run("adopt", repository, "--preview")
    assert preview.returncode == 0, preview.stderr
    assert f"test: `{expected}`" in preview.stdout
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


@pytest.mark.parametrize(
    "readme",
    [
        PAPER_LAB_UNITTEST,
        f"$env:PYTHONPATH = 'private'\n{PAPER_LAB_UNITTEST}",
        f"$env:PYTHONPATH = 'src'\n{PAPER_LAB_UNITTEST}; Write-Output private-fixture",
    ],
    ids=["missing-pythonpath", "different-pythonpath", "chained-command"],
)
def test_doctor_does_not_infer_paper_lab_check_from_partial_match(repository, readme):
    (repository / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    (repository / "README.md").write_text(f"```powershell\n{readme}\n```\n", encoding="utf-8")
    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert [item["command"] for item in report["commands"]] == ["python -m pytest"]
    assert "private-fixture" not in result.stdout


def test_doctor_reports_documented_powershell_test_suite(repository):
    (repository / "README.md").write_text(
        f"~~~powershell\n{PESTER_README_CHECK}\n~~~\n\n"
        "~~~powershell\npwsh -File .\\scripts\\Test-Vault.ps1 -VaultPath C:\\fixture-vault\n~~~\n",
        encoding="utf-8",
    )
    git(repository, "add", "application.txt")
    index = (repository / ".git/index").read_bytes()
    before = snapshot(repository)
    expected = (
        "Import-Module Pester -RequiredVersion 3.4.0; "
        r"$results = foreach ($suite in Get-ChildItem -LiteralPath .\vault\_system\tests "
        "-Filter '*.Tests.ps1') { Invoke-Pester -Script $suite.FullName -PassThru }; "
        "$results | Select-Object PassedCount, FailedCount; "
        "if (($results | Measure-Object FailedCount -Sum).Sum -gt 0) { throw 'Tests failed' }"
    )

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["commands"] == [
        {
            "name": "test:powershell",
            "command": expected,
            "source": "README.md",
            "verified": False,
        }
    ]
    assert "commands_unknown" not in {item["code"] for item in report["findings"]}
    assert report["checks_executed"] is False
    assert "fixture-vault" not in result.stdout
    preview = run("adopt", repository, "--preview")
    assert preview.returncode == 0, preview.stderr
    assert f"test:powershell: `{expected}`" in preview.stdout
    assert snapshot(repository) == before
    assert (repository / ".git/index").read_bytes() == index


@pytest.mark.parametrize(
    "instructions",
    [
        PESTER_README_CHECK.rsplit("\n", 1)[0],
        PESTER_README_CHECK.replace(r".\vault\_system\tests", r"C:\fixture-vault\tests"),
        PESTER_README_CHECK.replace("-PassThru", "-PassThru; Write-Output private-fixture"),
    ],
    ids=["missing-failure-check", "different-test-path", "extra-shell-command"],
)
def test_doctor_does_not_suggest_modified_powershell_test_blocks(repository, instructions):
    (repository / "README.md").write_text(f"~~~powershell\n{instructions}\n~~~\n", encoding="utf-8")

    result = run("doctor", repository, "--json")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["commands"] == []
    assert "commands_unknown" in {item["code"] for item in report["findings"]}
    assert "fixture-vault" not in result.stdout
    assert "private-fixture" not in result.stdout


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
