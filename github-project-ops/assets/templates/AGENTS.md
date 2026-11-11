# Project instructions

## Entry points

- For continuing work or changing scope, read [docs/HANDOFF.md](docs/HANDOFF.md).
- Use README.md for setup and release behavior, and pyproject.toml for tool configuration.
- Application code lives in src/; regression tests live in tests/.

## Development commands

Use Python 3.11+ in an activated virtual environment. Install development dependencies
with `python -m pip install -e ".[dev]"` when setup is part of the task.

- Tests: `python -m pytest` (target affected tests first).
- Lint: `python -m ruff check .`.
- Formatting: `python -m ruff format --check .`.
- Types: `python -m mypy src`.
- Distribution: `python -m build`.

These commands describe the starter; update them when the project's toolchain changes.
Their presence does not mean they have passed in the current checkout.

## Working agreements

- Define the requested outcome and acceptance evidence before substantial changes.
- Preserve unrelated edits and other sessions' work; check branch/worktree before integration.
- Continue ordinary reversible work within the user's authorized scope without repeated approval.
- Add regression coverage for changed behavior; run targeted checks before broader verification.
- Update relevant docs when public behavior, setup or release flow changes.
- Keep secrets, local configuration and generated artifacts out of commits.
- Keep publishing, deployment and live-data changes within the user's explicit scope.

## Completion and handoff

- Update docs/HANDOFF.md when scope, evidence, a blocker or the next action changes.
- Distinguish implemented, verified, integrated and deployed; record revision and evidence.
- Report failed, skipped or unavailable checks explicitly. Do not mark planned checks as passed.
- State the next concrete action and who can take it.
