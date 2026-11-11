# Changelog

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
