# Changelog

## 0.3.5 — 2026-11-11

### Changed

- For Python projects, `doctor` prefers `python312 -m mypy src` when the root
  `README.md` documents that exact command. Adopt previews use the same candidate.
  Mypy discovery falls back to `pyproject.toml` when the command is absent.
- Teo-tales-shaped fixtures cover inline and standalone commands, fallback, and
  read-only behavior.

## 0.3.4 — 2026-11-11

### Changed

- For npm projects, `doctor` prefers `npm ci --ignore-scripts` when the root
  `README.md` documents that exact command. Adopt previews use the same setup
  candidate. The default remains `npm ci` when the command is absent.
- Jev Advisor-shaped fixtures cover standalone and inline commands, fallback,
  and read-only behavior.

## 0.3.3 — 2026-11-11

### Added

- `doctor` suggests `pwsh -File ./scripts/check.ps1` for Godot projects with a
  regular, unlinked check script. It recognizes `project.godot` at the root or
  under `game/` and reports the command without running it.
- Regression fixtures cover both Godot layouts and verify that discovery leaves
  project files and the Git index unchanged.

## 0.3.2 — 2026-11-11

### Added

- In .NET repositories, `doctor` suggests `pwsh -File ./build-web.ps1` when the
  root script exists and `dotnet run --project` for `*.Tests.csproj` files with
  an explicit, unconditional `OutputType=Exe` in the bounded project scan.
- KidPic-shaped regression fixtures cover discovery, ambiguous project metadata,
  and read-only behavior. The suggested commands remain unverified.

## 0.3.1 — 2026-11-11

### Added

- `doctor` reports Mypy and Pyright candidates from `pyproject.toml`, using
  `uv run --locked` when the project has a `uv.lock`.
- Mypy uses configured targets when present and suggests the project root otherwise.
  Regression tests cover the Mypy and Pyright configurations found in both adoption pilots.

## 0.3.0 — 2026-11-11

### Added

- Read-only `doctor` with versioned JSON, Git/worktree inventory, bounded stack and
  command discovery, and actionable instruction/handoff findings.
- Additive `adopt --preview` with an independent provenance manifest, existing
  context selection, idempotence and protection for user files and linked paths.
- Concrete generated `AGENTS.md` and a shared handoff template separating
  implementation, verification, integration and deployment.
- Offline standard-library operation for doctor/adopt, without importing Copier.

## 0.2.0

### Added

- Copier-backed project generation with previews, saved answers, and MIT/no-license choices.
- Update previews and checked updates that preserve local edits and reject conflicts or ignored-file collisions.
- MIT repository license and complete generated license text.
- Deterministic skill ZIP archives, SHA-256 checksums, and GitHub Releases publication by version tag.
- YubiKey SSH signing setup and an agent workflow that preserves hardware confirmation.

- JSON scaffold reports and a generic profile for repositories without Python metadata.
- Installable Python starter package and a distribution smoke test.
- CI for Windows/Linux and Python 3.11/3.14, locked developer dependencies,
  Ruff checks, and type checking.
- Dependency update configuration for this repository and generated projects.
- Research notes comparing related GitHub projects and an explicit roadmap.

### Fixed

- Required paths must be readable, nonempty files rather than directories.
- Accept both `ci.yml` and `ci.yaml`; report malformed TOML and invalid repository paths.
- Release artifacts are tested before building, tags are checked against package
  metadata, and missing build artifacts fail the workflow.
