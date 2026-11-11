---
name: github-project-ops
description: Create a Python project, inspect or adopt an existing repository, update its scaffold, or prepare a release. Use for repository setup and maintenance, not ordinary application edits.
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
Use for a new or nearly empty repository. For Python projects, use `scripts/scaffold.py create` and its `--preview` mode; read `references/generator.md`. The Copier templates in `assets/templates/` render names, ownership, licensing, and saved answers consistently. For other stacks, adapt the relevant conventions.

### Audit mode
Use for an existing repository. Read `references/readiness.md` and run
`python scripts/scaffold.py doctor PATH --json` with the installed Python interpreter.
This is read-only; candidate commands have not been executed. Inspect relevant
findings before proposing changes. When onboarding is authorized, use
`adopt PATH --preview` and then `adopt PATH`; preserve existing instructions and use
`--handoff` to select an existing continuation document. Adoption does not create
a Copier baseline or authorize publishing, deployment or changes to other projects.

### Release mode
Use for version bumps, changelog updates, annotated tags, release notes, release artifacts, and GitHub release workflow updates.

### Maintenance mode
Use for CI/CD upkeep, contributor-experience improvements, docs refreshes, and keeping branching, tagging, and automation consistent over time.

## Workflow

1. Detect whether the request is `bootstrap`, `audit`, `release`, or `maintenance`.
2. Inspect the repository before changing it.
3. Read `references/repo-standards.md` when changing shared repository conventions.
4. Read `references/python-defaults.md` when creating or changing Python scaffolding.
5. Read `references/github-actions.md` when touching CI/CD, releases, artifacts, or publication.
6. For a Python bootstrap or generated-project update, follow `references/generator.md`. Preview changes first, then apply them within the user's request. Keep `.copier-answers.yml` in Git. Install, test, and build the result; do not copy raw `.jinja` inputs as finished project files.
7. Preserve coherent existing conventions unless the user asks to standardize aggressively.
8. For substantial work, agree on acceptance evidence and maintain one existing
   handoff/context document. Distinguish implemented, verified, integrated and
   deployed; state the next action without claiming unexecuted checks passed.

## Standard Outputs

When appropriate, scaffold or improve:

- `pyproject.toml`, `src/<package>/`, and a minimal package test for Python projects
- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `.editorconfig`
- `.gitignore`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/...`
- `.github/dependabot.yml` and `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

Create `CODEOWNERS`, `LICENSE`, or packaging/release extras when they fit the repository type and the user has not ruled them out.

## Guardrails

- Never overwrite major user-authored files blindly.
- Prefer minimal, working defaults over speculative enterprise patterns.
- Keep semver, branching, tagging, and release-note guidance explicit.
- Apply `$XDG_CONFIG_HOME`, cache, and state guidance only when the project actually manages runtime files.
- If the repository already uses another healthy stack or toolchain, adapt instead of forcing Python defaults.

## References

- Read `references/readiness.md` for read-only diagnosis, additive adoption and handoff.
- Read `references/repo-standards.md` for shared docs, branching, tagging, semver, release notes, artifacts, and XDG guidance.
- Read `references/generator.md` for creation, isolated diff previews, saved answers, and conflict-safe updates.
- Read `references/python-defaults.md` for `pyproject.toml`, `src/`, `pytest`, `ruff`, `mypy`, and packaging defaults.
- Read `references/github-actions.md` for GitHub Actions CI, release automation, and publishing guidance.

## Validation

After scaffolding, run `scripts/validate_scaffold.py <repo-path>` with Python 3.11+. Use `--public` for contributor and security docs, `--stack generic` for non-Python projects, and `--json` for automation. Exit codes are 0 (complete), 1 (missing or invalid files), and 2 (invalid invocation). This is a structural check; also run the resulting project's tests, quality checks, and build before calling a scaffold ready. The release template produces workflow artifacts; GitHub Release creation and package publication require separate configuration.
