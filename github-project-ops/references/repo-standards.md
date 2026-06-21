# Repo Standards

## Visibility Defaults

- Default to public repository conventions unless the user asks for private or internal behavior.
- Public repositories should include stronger contributor guidance, release hygiene, and security contact paths.
- Private repositories can keep the same structure but may slim down community-facing templates if they are noise.

## Core Files

Scaffold or improve these files when they fit the repository:

- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `CODEOWNERS`
- `.editorconfig`
- `.gitignore`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/`

Create a `LICENSE` only after checking whether the user has stated a preference. For public repositories, ask if no license choice is visible and the choice would affect downstream reuse.

## README And Documentation

- `README.md` should explain what the project is, who it is for, how to install or run it, how to develop it locally, and how releases work at a high level.
- `AGENTS.md` should capture repo-specific working rules for future agents, especially testing, formatting, branching, and release expectations.
- `CONTRIBUTING.md` should describe development setup, quality gates, branch and PR flow, and the expected review posture.
- `SECURITY.md` should explain how to report vulnerabilities and what the maintainer promises about handling them.

## Branching

- Prefer short-lived feature branches from the default branch.
- Name branches clearly, for example `feat/add-cli-config` or `fix/release-tagging`.
- Keep `main` or `master` releasable; avoid long-lived integration branches unless the repo already depends on them.

## Semantic Versioning

- Use semantic versioning by default.
- Patch: backward-compatible bug fixes.
- Minor: backward-compatible features.
- Major: breaking public API or behavior changes.

## Changelog, Tags, And Releases

- Keep `CHANGELOG.md` human-readable and grouped by release.
- Prefer an "Unreleased" section while work is in flight.
- Use annotated tags for releases.
- Keep release notes focused on user-visible changes, breaking changes, migration notes, and artifacts.
- Make artifact names predictable so GitHub releases are easy to navigate.

## GitHub Releases And Artifacts

- Release notes should map to the changelog, not invent a second incompatible source of truth.
- Libraries usually publish wheels and source distributions.
- CLI projects may attach zipped or tarred binaries as release artifacts.
- Application repos should state whether artifacts are packages, containers, installers, or deployment bundles.

## XDG-Aware Runtime Layout

Use XDG guidance when the project stores runtime files:

- `$XDG_CONFIG_HOME` for user-editable configuration
- `$XDG_CACHE_HOME` for disposable cache data
- `$XDG_STATE_HOME` for non-portable runtime state
- `$XDG_DATA_HOME` for durable app data

Do not force XDG complexity onto a pure library that does not manage local runtime state.
