"""Read-only project discovery and additive adoption. No project code is executed."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import stat
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

SCAFFOLD_VERSION = "0.3.7"
MANIFEST = ".scaffold.json"
DEFAULT_HANDOFF = "docs/HANDOFF.md"
MAX_FILE_BYTES = 1_048_576
INSTRUCTIONS = ("AGENTS.md", "AGENTS.override.md", "AGENT.md", "CLAUDE.md")


def linked(path: Path) -> bool:
    """Include Windows junctions/reparse points, even on Python 3.11."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def safe_path(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if (
        not name
        or any(ord(character) < 32 for character in name)
        or relative.is_absolute()
        or "\\" in name
        or ":" in name
        or any(part.casefold() in ("..", ".git") for part in relative.parts)
        or relative.as_posix() != name
    ):
        raise ValueError(f"Unsafe project-relative path: {name}")
    current = root
    for part in relative.parts:
        current = current / part
        if linked(current):
            raise ValueError(f"Symbolic link/reparse point requires manual handling: {name}")
    if not current.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes the project: {name}")
    return current


def read_text(root: Path, name: str) -> str:
    path = safe_path(root, name)
    if not path.is_file():
        raise ValueError(f"Expected a regular file: {name}")
    with path.open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"File exceeds inspection limit: {name}")
    return data.decode("utf-8-sig")


def git_read(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if result.returncode:
        # Do not echo arbitrary Git diagnostics (which can contain private URLs).
        raise ValueError(f"Git inspection failed: {args[0]}")
    return result.stdout.strip()


def existing_directory(destination: Path) -> Path:
    if linked(destination):
        raise ValueError("Destination must not be a symbolic link/reparse point")
    root = destination.resolve()
    if not root.is_dir():
        raise ValueError("Destination must be an existing directory")
    return root


def load_manifest(root: Path) -> dict[str, Any] | None:
    path = root / MANIFEST
    if not path.exists() and not linked(path):
        return None
    data = json.loads(read_text(root, MANIFEST))
    if (
        not isinstance(data, dict)
        or type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
        or not isinstance(data.get("scaffold_version"), str)
        or not isinstance(data.get("created_files"), dict)
        or not isinstance(data.get("handoff"), str)
    ):
        raise ValueError("Invalid or unsupported .scaffold.json schema")
    validate_handoff(root, data["handoff"])
    for name, digest in data["created_files"].items():
        safe_path(root, name)
        if name not in ("AGENTS.md", data["handoff"]):
            raise ValueError("Unexpected created file in .scaffold.json")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("Invalid digest in .scaffold.json")
        try:
            int(digest, 16)
        except ValueError as error:
            raise ValueError("Invalid digest in .scaffold.json") from error
    return data


def validate_handoff(root: Path, name: str) -> Path:
    path = safe_path(root, name)
    if path.suffix.lower() != ".md" or path.name.casefold() in {
        name.casefold() for name in INSTRUCTIONS
    }:
        raise ValueError("Handoff must be a separate project-relative Markdown file")
    if any(part.startswith(".") for part in PurePosixPath(name).parts):
        raise ValueError("Handoff must not be inside a hidden directory")
    return path


def executable_dotnet_test(root: Path, project_file: str) -> bool:
    try:
        text = read_text(root, project_file)
        if "<!DOCTYPE" in text:
            return False
        project = ET.fromstring(text)
    except (OSError, ValueError, ET.ParseError):
        return False

    if project.tag.rsplit("}", 1)[-1] != "Project":
        return False
    outputs = project.findall(".//{*}OutputType")
    if len(outputs) != 1:
        return False
    output = outputs[0]
    return (
        (output.text or "").strip().casefold() == "exe"
        and "Condition" not in output.attrib
        and any(
            "Condition" not in group.attrib and group.find("{*}OutputType") is output
            for group in project.findall("{*}PropertyGroup")
        )
    )


def readme_documents_command(
    root: Path, command: str, *, allow_line_comments: bool = False
) -> bool:
    try:
        readme = read_text(root, "README.md")
    except (OSError, ValueError):
        return False

    lines = [
        r"[ \t]+".join(re.escape(part) for part in line.split()) for line in command.splitlines()
    ]
    line_end = r"(?:[ \t]+#[^\r\n]*)?[ \t]*" if allow_line_comments else r"[ \t]*"
    invocation = rf"{line_end}\r?\n[ \t]*".join(lines)
    standalone = rf"^[ \t]*{invocation}{line_end}\r?$"
    if len(lines) == 1:
        inline_code = rf"(?<!`)`[ \t]*{invocation}[ \t]*`(?!`)"
        standalone = f"{standalone}|{inline_code}"
    return re.search(standalone, readme, re.MULTILINE) is not None


def inspect_project(destination: Path) -> dict[str, Any]:
    requested = existing_directory(destination)
    root = requested
    findings: list[dict[str, str]] = []

    def finding(code: str, message: str, severity: str = "warning") -> None:
        findings.append({"code": code, "severity": severity, "message": message})

    git_info: dict[str, Any] = {"root": None, "head": None, "branch": None, "worktrees": []}
    try:
        root = Path(git_read(requested, "rev-parse", "--show-toplevel")).resolve()
        git_info["root"] = str(root)
        if root != requested:
            finding("not_git_root", "Requested directory is inside a repository; use its root.")
        try:
            git_info["head"] = git_read(root, "rev-parse", "--verify", "HEAD")
        except ValueError:
            finding("no_commit", "Repository has no readable HEAD commit.")
        try:
            git_info["branch"] = git_read(root, "symbolic-ref", "--quiet", "--short", "HEAD")
        except ValueError:
            finding("detached_head", "Checkout has a detached HEAD.", "info")
        status = git_read(root, "status", "--porcelain=v1", "-z", "--untracked-files=normal")
        git_info["dirty"] = bool(status)
        if status:
            finding("working_changes", "Working changes exist; preserve their ownership.", "info")
        raw_worktrees = git_read(root, "worktree", "list", "--porcelain", "-z")
        git_info["worktrees"] = [
            field.removeprefix("worktree ")
            for field in raw_worktrees.split("\0")
            if field.startswith("worktree ")
        ]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        finding("git_unavailable", "No readable Git repository, or Git inspection is unavailable.")
        # Only suggest immediate child roots; never recursively walk runtime data.
        git_info["nested_roots"] = [
            str(child)
            for child in sorted(requested.iterdir())
            if not linked(child) and child.is_dir() and (child / ".git").exists()
        ]

    stacks: list[str] = []
    commands: list[dict[str, Any]] = []

    def command(name: str, value: str, source: str) -> None:
        commands.append({"name": name, "command": value, "source": source, "verified": False})

    if (root / "pyproject.toml").exists():
        stacks.append("python")
        try:
            pyproject = tomllib.loads(read_text(root, "pyproject.toml"))
            config = pyproject.get("tool", {})
            if not isinstance(config, dict):
                raise TypeError("Invalid tool configuration")
            # Infer only from explicit configuration, not installed executables.
            prefix = "uv run --locked" if (root / "uv.lock").is_file() else "python -m"
            paper_lab_check = (
                "$env:PYTHONPATH = 'src'\n"
                r"& '.\.venv-paper\Scripts\python.exe' -m unittest discover -s tests -q"
            )
            if readme_documents_command(root, paper_lab_check):
                command("test", "; ".join(paper_lab_check.splitlines()), "README.md")
            elif "pytest" in config:
                command("test", f"{prefix} pytest", "pyproject.toml [tool.pytest]")
            if "ruff" in config:
                command("lint", f"{prefix} ruff check .", "pyproject.toml [tool.ruff]")
                command(
                    "format-check", f"{prefix} ruff format --check .", "pyproject.toml [tool.ruff]"
                )
            mypy = config.get("mypy")
            documented_mypy = "python312 -m mypy src"
            if readme_documents_command(root, documented_mypy):
                command("mypy", documented_mypy, "README.md")
            elif isinstance(mypy, dict):
                # Let mypy resolve configured targets without copying them into a shell command.
                has_targets = any(mypy.get(key) for key in ("files", "modules", "packages"))
                target = "" if has_targets else " ."
                command("mypy", f"{prefix} mypy{target}", "pyproject.toml [tool.mypy]")
            if isinstance(config.get("pyright"), dict):
                command("pyright", f"{prefix} pyright", "pyproject.toml [tool.pyright]")
            if (root / "uv.lock").is_file():
                command("bootstrap", "uv sync --locked", "uv.lock")
        except (OSError, ValueError, TypeError) as error:
            finding(
                "invalid_python_metadata",
                f"Cannot inspect pyproject.toml ({type(error).__name__}).",
            )

    if (root / "package.json").exists():
        stacks.append("node")
        try:
            package = json.loads(read_text(root, "package.json"))
            if not isinstance(package, dict) or not isinstance(package.get("scripts", {}), dict):
                raise TypeError("Invalid scripts")
            managers = [
                manager
                for lock, manager in (
                    ("package-lock.json", "npm"),
                    ("pnpm-lock.yaml", "pnpm"),
                    ("yarn.lock", "yarn"),
                )
                if (root / lock).is_file()
            ]
            if len(managers) != 1:
                finding(
                    "package_manager_unknown", "Select one package manager/lockfile before setup."
                )
            else:
                manager = managers[0]
                scripts = package.get("scripts", {})
                for name in ("test", "check", "lint", "build", "test:browser", "smoke"):
                    if not isinstance(scripts.get(name), str):
                        continue
                    if (
                        manager == "npm"
                        and name == "test:browser"
                        and isinstance(scripts.get("build"), str)
                    ):
                        build = "npm run build"
                        browser_test = "npm run test:browser"
                        sequence = f"{build} && {browser_test}"
                        if readme_documents_command(
                            root, f"{build}\n{browser_test}", allow_line_comments=True
                        ) or readme_documents_command(root, sequence):
                            command(name, sequence, "README.md")
                            continue
                    command(name, f"{manager} run {name}", f"package.json scripts.{name}")
                if manager == "npm":
                    documented_npm = "npm ci --ignore-scripts"
                    if readme_documents_command(root, documented_npm):
                        command("bootstrap", documented_npm, "README.md")
                    else:
                        command("bootstrap", "npm ci", "package-lock.json")
        except (OSError, ValueError, TypeError) as error:
            finding(
                "invalid_node_metadata", f"Cannot inspect package.json ({type(error).__name__})."
            )

    # Detect .NET files in the root and one level below it, without traversing
    # caches, linked directories, or arbitrary nested source trees.
    children = [child for child in root.iterdir() if not linked(child)]
    dotnet = [
        child
        for child in children
        if child.is_file() and child.suffix in (".csproj", ".sln", ".slnx")
    ]
    for child in children:
        if (
            child.is_dir()
            and not child.name.startswith(".")
            and child.name
            not in ("node_modules", "vendor", "dist", "build", "artifacts", "bin", "obj")
        ):
            dotnet.extend(p for p in child.glob("*.csproj") if not linked(p) and p.is_file())
    if dotnet:
        stacks.append("dotnet")
        build_script = root / "build-web.ps1"
        if build_script in children and build_script.is_file():
            command("build", "pwsh -File ./build-web.ps1", "build-web.ps1")
        for project in sorted(dotnet):
            if project.suffix != ".csproj" or not project.stem.casefold().endswith(".tests"):
                continue
            relative = project.relative_to(root).as_posix()
            # Only render paths that are safe to copy into a shell command.
            if not re.fullmatch(r"[A-Za-z0-9_. /-]+", relative):
                continue
            if executable_dotnet_test(root, relative):
                target = f'"./{relative}"' if " " in relative else f"./{relative}"
                command("test", f"dotnet run --project {target}", f"{relative} [OutputType=Exe]")
    for marker, stack in (
        ("project.godot", "godot"),
        ("game/project.godot", "godot"),
        ("main.tf", "terraform"),
        ("terragrunt.hcl", "terraform"),
        ("ansible.cfg", "ansible"),
    ):
        if (root / marker).is_file() and stack not in stacks:
            stacks.append(stack)
    if "godot" in stacks:
        check_script = "scripts/check.ps1"
        try:
            has_check_script = safe_path(root, check_script).is_file()
        except (OSError, ValueError):
            has_check_script = False
        if has_check_script:
            command("check", f"pwsh -File ./{check_script}", check_script)
    instructions = [name for name in INSTRUCTIONS if (root / name).exists() or linked(root / name)]
    for name in instructions:
        try:
            if not read_text(root, name).strip():
                finding("empty_instructions", f"{name} is empty.")
        except (OSError, ValueError):
            finding("unreadable_instructions", f"{name} is not a readable regular UTF-8 file.")
    if "AGENTS.md" not in instructions and "AGENTS.override.md" not in instructions:
        finding("missing_agents", "No AGENTS.md or AGENTS.override.md at the project root.")
    if "AGENTS.override.md" in instructions:
        finding("agents_override", "AGENTS.override.md takes precedence over AGENTS.md.", "info")
    if not commands:
        finding(
            "commands_unknown",
            "No check commands inferred; document the existing project commands.",
        )

    adoption = None
    handoff = DEFAULT_HANDOFF
    try:
        adoption = load_manifest(root)
        if adoption:
            handoff = adoption["handoff"]
            for name in adoption["created_files"]:
                if not safe_path(root, name).is_file():
                    finding("missing_adopted_file", f"Previously created file is missing: {name}")
        if not read_text(root, handoff).strip():
            finding("empty_handoff", f"{handoff} is empty.")
    except (OSError, ValueError):
        if adoption is None and ((root / MANIFEST).exists() or linked(root / MANIFEST)):
            finding("invalid_adoption", "Cannot read or validate .scaffold.json.", "error")
        else:
            finding(
                "missing_handoff",
                f"No readable handoff at {handoff}; select existing context with adopt --handoff.",
            )

    return {
        "schema_version": 1,
        "requested_path": str(requested),
        "root": str(root),
        "git": git_info,
        "stacks": stacks or ["unknown"],
        "commands": commands,
        "instructions": instructions,
        "handoff": handoff,
        "adoption": adoption,
        "copier": (root / ".copier-answers.yml").is_file(),
        "findings": findings,
        "checks_executed": False,
    }


def doctor_project(destination: Path, *, as_json: bool) -> int:
    try:
        report = inspect_project(destination)
    except (OSError, ValueError, TypeError) as error:
        if not as_json:
            raise
        print(json.dumps({"schema_version": 1, "error": str(error)}, ensure_ascii=True))
        return 2
    if as_json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(f"Project: {report['root']}\nStacks: {', '.join(report['stacks'])}")
        for item in report["commands"]:
            print(f"Candidate {item['name']}: {item['command']} ({item['source']}; unverified)")
        for item in report["findings"]:
            print(f"{item['severity']}: {item['code']}: {item['message']}")
        print("Project code and checks were not executed. No files were changed.")
    return 1 if any(f["severity"] != "info" for f in report["findings"]) else 0


def render_agents(report: dict[str, Any], handoff: str) -> str:
    commands = (
        "\n".join(
            f"- {item['name']}: `{item['command']}` (from {item['source']}; not yet verified)."
            for item in report["commands"]
        )
        or "- Commands are not established. Inspect the README and existing build/test scripts first."
    )
    existing_guidance = "".join(
        f"- Existing guidance: [{name}]({name}); preserve its relevant project conventions.\n"
        for name in report["instructions"]
        if name in ("AGENT.md", "CLAUDE.md")
    )
    return f"""# Project instructions

## Entry points

- For continuing work or changing scope, read [the current handoff]({quote(handoff, safe="/")}).
- Use the existing README for setup and architecture; read specialist docs only when relevant.
- Detected stack: {", ".join(report["stacks"])}. Preserve the existing toolchain.

{existing_guidance}
## Candidate commands

These were inferred from metadata, not run. Confirm their prerequisites and side effects
before using them; replace this list with verified project commands as work proceeds.

{commands}

## Working agreements

- Define the requested outcome and its acceptance evidence before substantial changes.
- Preserve unrelated edits and other sessions' work. Check the branch/worktree before integrating.
- Continue ordinary reversible work within the user's authorized scope without repeated approval.
- Use targeted checks for changed behavior; broaden verification when the change warrants it.
- Keep secrets, personal data, local configuration and generated artifacts out of commits.
- Publishing, deployment and live-data changes must stay within the user's explicit scope.

## Completion and handoff

- Update the linked handoff when scope, evidence, a blocker, or the next action changes.
- Separate implemented, verified, integrated and deployed. Do not infer one from another.
- Record the revision, commands and outcomes; mark unavailable or skipped checks explicitly.
- State the next concrete action and who can take it. A planned test is not evidence.
"""


def render_handoff() -> str:
    template = Path(__file__).resolve().parents[1] / "assets/templates/docs/HANDOFF.md"
    return template.read_text(encoding="utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_additions(root: Path, additions: dict[str, bytes]) -> None:
    """Preflight all paths, create exclusively, roll back only our own bytes on error."""
    for name in additions:
        path = safe_path(root, name)
        if path.exists():
            raise ValueError(f"Adoption would overwrite an existing path: {name}")
        for parent in path.parents:
            if parent == root:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"Adoption path crosses a non-directory: {name}")
    created: list[tuple[Path, bytes]] = []
    directories: list[Path] = []
    try:
        for name, contents in additions.items():
            path = safe_path(root, name)
            for parent in reversed(path.parents):
                if parent.is_relative_to(root) and not parent.exists():
                    parent.mkdir()
                    directories.append(parent)
            with path.open("xb") as stream:
                created.append((path, contents))
                stream.write(contents)
    except (OSError, ValueError):
        for path, contents in reversed(created):
            if not linked(path) and path.is_file() and path.read_bytes() == contents:
                path.unlink()
        for directory in reversed(directories):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def adopt_project(destination: Path, *, preview: bool, handoff: str | None) -> int:
    root = existing_directory(destination)
    git_root = Path(git_read(root, "rev-parse", "--show-toplevel")).resolve()
    if git_root != root:
        raise ValueError("Adopt must target the Git repository root")
    if (root / ".copier-answers.yml").exists() or linked(root / ".copier-answers.yml"):
        raise ValueError("Copier-generated project: use update instead of adopt")
    existing = load_manifest(root)
    if existing:
        if handoff is not None and handoff != existing["handoff"]:
            raise ValueError(
                "Already adopted with a different handoff; review .scaffold.json manually"
            )
        print(
            "Already adopted. Existing files and user edits preserved; use doctor to inspect readiness."
        )
        return 0
    handoff_name = handoff or DEFAULT_HANDOFF
    handoff_path = validate_handoff(root, handoff_name)
    if handoff is not None and not handoff_path.is_file():
        raise ValueError("--handoff must select an existing Markdown context file")
    additions: dict[str, bytes] = {}
    preserved: list[str] = []
    for name in INSTRUCTIONS:
        path = safe_path(root, name)
        if path.exists():
            if not read_text(root, name).strip():
                raise ValueError(f"Existing instruction file is empty: {name}")
            preserved.append(name)
    if "AGENTS.md" not in preserved and "AGENTS.override.md" not in preserved:
        additions["AGENTS.md"] = render_agents(inspect_project(root), handoff_name).encode("utf-8")
    if handoff_path.exists():
        if not read_text(root, handoff_name).strip():
            raise ValueError("Existing handoff is empty; populate it before adopting")
        preserved.append(handoff_name)
    else:
        additions[handoff_name] = render_handoff().encode("utf-8")
    manifest = {
        "schema_version": 1,
        "scaffold_version": SCAFFOLD_VERSION,
        "handoff": handoff_name,
        "created_files": {name: digest(contents) for name, contents in additions.items()},
    }
    additions[MANIFEST] = (json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    # Preflight even previews; they must not suggest an impossible/unsafe application.
    for name in additions:
        path = safe_path(root, name)
        if path.exists() or any(p.exists() and not p.is_dir() for p in path.parents if p != root):
            raise ValueError(f"Adoption path is occupied: {name}")
    for name in preserved:
        print(f"Preserve: {name}")
    if "AGENTS.md" in preserved or "AGENTS.override.md" in preserved:
        print(
            f"Review existing instructions for a link to {handoff_name}; they will not be edited."
        )
    if preview:
        for name, contents in additions.items():
            print(
                "".join(
                    difflib.unified_diff(
                        [],
                        contents.decode("utf-8").splitlines(keepends=True),
                        fromfile="/dev/null",
                        tofile=name,
                    )
                ),
                end="",
            )
        return 0
    write_additions(root, additions)
    print(
        "Adopted. Review the added files and fill in the handoff; no checks or Git writes were run."
    )
    return 0
