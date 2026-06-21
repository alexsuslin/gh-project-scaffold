# Python Defaults

## Packaging

- Prefer `pyproject.toml` as the project metadata and tool configuration entry point.
- Prefer `src/` layout for packages that will be imported or distributed.
- Keep metadata explicit: project name, version, description, Python requirement, readme, and classifiers when useful.

## Testing And Quality

- Use `pytest` for tests.
- Use `ruff` for linting and formatting when that fits the repo.
- Use `mypy` when static types improve confidence or public API stability.
- Keep commands easy to discover in docs and CI.

## Dependency Hygiene

- Keep runtime dependencies separate from development dependencies.
- Avoid heavy packaging machinery unless the project truly needs it.
- Prefer one clear toolchain over multiple overlapping tools that solve the same job.

## Suggested Layout

```text
project-root/
  pyproject.toml
  README.md
  src/
    package_name/
      __init__.py
  tests/
```

## CLI And App Considerations

- If the repo is a CLI or application, add an entry point in `pyproject.toml`.
- If the app stores local files, follow the XDG guidance from `references/repo-standards.md`.
- If the repo is only a library, keep runtime file handling out of the default scaffold.
