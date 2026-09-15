# Python Defaults

Use `pyproject.toml`, a `src/` package, and a small test suite. Preserve an
existing healthy backend or dependency manager. The bundled Copier template uses
Hatchling, supports Python 3.11+, and separates runtime dependencies from the
`dev` extra.

## Generate and verify

Follow [generator.md](generator.md) for `create --preview`, creation, and updates.
Names, module paths, README, ownership, license, and saved answers are rendered
together. Files ending in `.jinja` are template inputs, not files to copy unchanged.

After generation:

```sh
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
```

The starter test checks the installed distribution and importable package.
Replace it with useful behavior tests as the project grows. This repository's
integration test builds the rendered sample into an sdist/wheel, installs the
wheel in a clean environment, and imports it outside the source checkout.

For existing repositories, adapt individual guidance instead of running create
over existing files. Non-Python repositories should keep their current toolchain
and use the validator's `--stack generic` profile.

## Compatibility and dependencies

Keep the minimum Python version aligned across metadata, Ruff, mypy, and CI.
The sample tests Python 3.11 and 3.14 on Linux and Windows.

Use a lockfile for reproducible application/developer environments when useful.
Library runtime ranges and developer lockfiles serve different purposes.
The root repository uses uv; generated projects do not require it.
Dependabot maintains Python requirements and workflow Actions.

## Runtime files

Add a `[project.scripts]` entry only when there is an actual CLI entry point.
Apply XDG config/cache/state/data guidance only to applications storing runtime
files; do not add it to a pure library.