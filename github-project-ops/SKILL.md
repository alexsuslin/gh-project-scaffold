---
name: github-project-ops
description: Use when creating, auditing, maintaining, or releasing a GitHub-hosted software project and Codex needs Python-first repository scaffolding, README.md and contributor docs, CI/CD workflows, semantic versioning, branching, tagging, release notes, artifacts, AGENTS.md guidance, or XDG-aware project conventions.
---

# Github Project Ops

## Overview

Use this skill to bootstrap or improve a repository so it is easier to build, test, release, and contribute to over time. Default to Python-first and public-project conventions unless the user asks for a different stack, privacy posture, or release policy.

## Defaults

- Python-first
- Public by default
- GitHub-first automation
- Semantic versioning
- Minimal working scaffolds over heavy boilerplate

Treat `public` or `private`, `python` or another stack, and `bootstrap`, `audit`, `release`, or `maintenance` as parameters inferred from the request. Ask only when the choice changes user-facing files, publishing behavior, or compatibility.

## Modes

### Bootstrap mode
Use for a new or nearly empty repository. Scaffold the core project files directly when asked, using the templates in `assets/templates/` as the starting point.

### Audit mode
Use for an existing repository. Inspect current files first, identify missing or weak conventions, and patch incrementally instead of replacing working user-authored structure.

### Release mode
Use for version bumps, changelog updates, annotated tags, release notes, release artifacts, and GitHub release workflow updates.

### Maintenance mode
Use for CI/CD upkeep, contributor-experience improvements, docs refreshes, and keeping branching, tagging, and automation consistent over time.

## Workflow

1. Detect whether the request is `bootstrap`, `audit`, `release`, or `maintenance`.
2. Inspect the repository before changing it.
3. Read `references/repo-standards.md` for shared standards.
4. Read `references/python-defaults.md` when the project is Python or the user has not specified another stack.
5. Read `references/github-actions.md` when touching CI/CD, releases, artifacts, or publication.
6. Copy or adapt files from `assets/templates/` instead of regenerating common boilerplate from scratch.
7. Preserve coherent existing conventions unless the user asks to standardize aggressively.

## Standard Outputs

When appropriate, scaffold or improve:

- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `.editorconfig`
- `.gitignore`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/...`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

Create `CODEOWNERS`, `LICENSE`, or packaging/release extras when they fit the repository type and the user has not ruled them out.

## Guardrails

- Never overwrite major user-authored files blindly.
- Prefer minimal, working defaults over speculative enterprise patterns.
- Keep semver, branching, tagging, and release-note guidance explicit.
- Apply `$XDG_CONFIG_HOME`, cache, and state guidance only when the project actually manages runtime files.
- If the repository already uses another healthy stack or toolchain, adapt instead of forcing Python defaults.

## References

- Read `references/repo-standards.md` for shared docs, branching, tagging, semver, release notes, artifacts, and XDG guidance.
- Read `references/python-defaults.md` for `pyproject.toml`, `src/`, `pytest`, `ruff`, `mypy`, and packaging defaults.
- Read `references/github-actions.md` for GitHub Actions CI, release automation, and publishing guidance.

## Validation

After scaffolding, run `scripts/validate_scaffold.py <repo-path>` to confirm the minimum expected repository structure. Use `--public` when validating a public-facing scaffold that should include contributor and security docs.
