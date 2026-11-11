# Project instructions

## Entry points

- For continuing work or changing scope, read [docs/HANDOFF.md](docs/HANDOFF.md).
- CLI entry point: github-project-ops/scripts/scaffold.py; doctor/adopt live in project_readiness.py.
- Templates: github-project-ops/assets/templates/. Readiness contract: github-project-ops/references/readiness.md.
- Use CONTRIBUTING.md for setup and docs/releases.md when preparing a release.

## Development commands

Use the existing environment. Standard setup is `uv sync --locked`. On this Windows
host, run modules through `.venv/Scripts/python.exe` if entry-point executables are
blocked; keep OS security enabled. Set UV_CACHE_DIR inside tmp-test-runs/ if the
default cache is inaccessible. Test fixtures use synthetic Git identities and must
stay in temporary directories; never run adoption against other personal projects
unless the user explicitly includes them in the task.

- Tests: `python -m pytest`; use a fresh `--basetemp=tmp-test-runs/NAME` if needed.
- Lint: `python -m ruff check .`.
- Formatting: `python -m ruff format --check .`.
- Types: `python -m mypy github-project-ops/scripts scripts`.
- Release archive: `python scripts/build_release.py --tag vVERSION --output-dir dist`;
  replace VERSION with the contents of the VERSION file. This does not publish.
- Keep VERSION, pyproject.toml, uv.lock and project_readiness.SCAFFOLD_VERSION aligned.

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
