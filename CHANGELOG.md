# Changelog

## Unreleased

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