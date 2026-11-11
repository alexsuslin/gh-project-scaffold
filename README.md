# gh-project-scaffold

A project-readiness CLI, Codex skill and Copier generator for GitHub-ready Python projects.
Create a project with a diff preview, then bring later template improvements into
it without overwriting local work silently.

## Features

- Read-only `doctor` with text/JSON reports for existing projects and worktrees.
- Additive `adopt --preview`, preserving existing instructions and context files.
- Concrete `AGENTS.md` entry points and a handoff separating implementation, verification and delivery.
- `create --preview`: see the generated files before writing anything.
- `update --preview`: calculate a three-way template update in an isolated clone.
- Saved names, ownership, visibility, license, and template revision in `.copier-answers.yml`.
- Working Python package with pytest, Ruff, mypy, wheel/sdist builds, and Linux/Windows CI.
- Conflict detection and protection for ignored local files.
- Standalone structural validator with JSON output and a non-Python profile.
- Versioned skill ZIPs and checksums published through GitHub Releases.
- MIT license.

## Inspect and adopt an existing project

Requires Python 3.11+ and Git; these two commands need no Python dependencies or
network access. Use your installed Python interpreter (on Windows, an explicit
path may be needed instead of the WindowsApps alias).

```sh
python github-project-ops/scripts/scaffold.py doctor path/to/project --json
python github-project-ops/scripts/scaffold.py adopt path/to/project --preview
python github-project-ops/scripts/scaffold.py adopt path/to/project
```

`doctor` discovers the Git root, branch, working changes, worktrees, stack markers,
candidate commands, instruction files and handoff. It does not execute project code,
install packages, contact remotes or claim that checks passed. Exit codes: 0 no
warnings/errors, 1 findings to review, 2 invalid input or operational failure.

`adopt` targets an existing Git root, including one with uncommitted work. It adds
missing `AGENTS.md`, `docs/HANDOFF.md` and a `.scaffold.json` provenance manifest.
Existing files are preserved, including `AGENTS.override.md`. For an existing
context document use `--handoff docs/CONTEXT.md` on the first adoption. Review any
existing instructions for a link to that document; they are not automatically edited.
Repeated adoption is a no-op, including after you edit the new files.

This is additive onboarding, not a Copier migration. It does not create
`.copier-answers.yml` or enable Copier `update` for an unrelated project. Record
the real goal and evidence in the handoff after adoption. See the
[readiness guide](github-project-ops/references/readiness.md) for discovery limits,
JSON fields, path safety and recovery.

## Create a project

Requires Git and [uv](https://docs.astral.sh/uv/getting-started/installation/).
From a checkout:

```sh
uv run github-project-ops/scripts/scaffold.py create ../weather-kit --name weather-kit --owner YOUR_GITHUB_LOGIN --preview
uv run github-project-ops/scripts/scaffold.py create ../weather-kit --name weather-kit --owner YOUR_GITHUB_LOGIN
```

The script pins its Copier dependency and requires Python 3.11+.
Use `--package`, `--description`, `--visibility private`, or `--license none`
to customize the result. The default template source is this GitHub repository's
latest release; `--source PATH_OR_URL --ref TAG` selects another versioned source.
A release containing the new generator/template must be pushed before those
defaults are available remotely.

Create requires an empty target (an existing `.git` is allowed). Preview leaves
the target and its parents untouched. After creation, follow the generated README
to install dependencies and run checks, then commit the project including its answers.

## Update a generated project

Start with a clean, committed Git repository:

```sh
uv run github-project-ops/scripts/scaffold.py update ../weather-kit --preview
uv run github-project-ops/scripts/scaffold.py update ../weather-kit
```

Copier performs the merge in a temporary clone. The wrapper validates the prepared
paths before applying them. Conflicts return code 3 and leave the project unchanged;
ignored-file collisions also stop the update. A successful update leaves a diff
for review and a user-signed commit.

See [the generator guide](github-project-ops/references/generator.md) for pinned
versions, manual conflict resolution, saved answers, and limitations.

## Install as a Codex skill

Copy `github-project-ops/` from the repository or a verified release archive into
your Codex skills directory. Review any existing installation before replacing it.

PowerShell (default Codex home):

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse .\github-project-ops "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux:

```sh
mkdir -p ~/.codex/skills
cp -R github-project-ops ~/.codex/skills/
```

Use your configured `CODEX_HOME/skills` when different. Example request:

> Use $github-project-ops to create a public Python library with a preview first.

The skill also audits existing repositories and adapts to other stacks. The
Copier generator itself currently targets Python. `adopt` adds guidance to other
stacks without converting their structure or creating a Copier baseline.

## Validate a project

The validator requires Python 3.11+ and no third-party packages:

```sh
python github-project-ops/scripts/validate_scaffold.py path/to/project --public --json
python github-project-ops/scripts/validate_scaffold.py path/to/node-project --stack generic
```

| Profile | Required files |
| --- | --- |
| Python (default) | README, pyproject.toml, CI workflow named ci.yml or ci.yaml |
| `--stack generic` | README and CI workflow |
| `--public` | Also CONTRIBUTING.md and SECURITY.md |

Files must be readable, nonempty UTF-8; Python TOML syntax is checked.
This does not replace tests, builds, or workflow validation.
JSON fields are `ok`, `root`, `stack`, `public`, `missing`, and `errors`.
Exit codes: 0 valid, 1 incomplete/invalid files, 2 invalid invocation/path.

## Development and releases

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy github-project-ops/scripts scripts
```

Tests exercise creation, previews, update conflicts, preserved user files, and
building/installing the rendered package. See [CONTRIBUTING.md](CONTRIBUTING.md).

[Release instructions](docs/releases.md) cover version tags, archives, checksums,
and the automatic GitHub Release workflow. The generated Python project's
separate release workflow builds package artifacts; it does not publish to PyPI.

[YubiKey and agent workflow](docs/yubikey-agent-workflow.md) explains how to keep
hardware signing while letting an agent prepare and test changes.

## Design background

[Research notes](docs/research-and-roadmap.md) explain the ideas adopted from
Scientific Python, Hypermodern Python, and Copier. Licensed under [MIT](LICENSE).
