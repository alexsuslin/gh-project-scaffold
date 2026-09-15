# Contributing

Use Python 3.11+ and uv. Install the development environment with
`uv sync --locked`. The validator uses only the standard library; the generator uses Copier.

Before opening a pull request, run:

```sh
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy github-project-ops/scripts scripts
uv run --locked pytest
```

Use `uv run ruff format .` to apply formatting. To update dependencies, run
`uv lock --upgrade`, rerun the checks, and include `uv.lock` in the change.

Tests build the Python template into a source distribution and wheel, install
the wheel in an isolated environment, and import it outside the source checkout.
Keep those tests passing when changing template paths, metadata, or packaging.
Use pytest's `tmp_path` for disposable fixtures; do not modify installed skills.

If your local system temporary directory is inaccessible, pass a fresh directory
inside `tmp-test-runs/` via `pytest --basetemp=tmp-test-runs/my-run`.
Pytest clears a supplied basetemp directory, so never point it at existing work.

Keep changes focused and describe the observable behavior and checks in the PR.
Update the README and skill references when command-line behavior changes.
When updating Actions, update both the repository workflows and the bundled
workflow templates; the root Dependabot Actions job only maintains root workflows.
Render the Copier template before testing it; files ending in .jinja are not
standalone Python project files. Generator tests use isolated Git repositories
and synthetic unsigned fixture commits; they never change your signing settings.
Keep template Python dependency ranges current manually: Dependabot cannot read
the unrendered pyproject.toml.jinja manifest.
