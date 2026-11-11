# Handoff

Current continuation point after the 0.3.0 project-readiness pilots. Command contracts
and limitations are documented in [the readiness guide](../github-project-ops/references/readiness.md).

## Outcome and acceptance

- Current goal: release v0.3.4 with README-aware npm setup discovery.
- Acceptance: align version metadata, verify the packaged doctor on an npm
  fixture, and confirm main CI and publication for the signed release commit.
- Scope: project-scaffolding and synthetic fixtures only.

## Current state

- Last substantive update: 2026-11-11.
- Published baseline: [v0.3.3](https://github.com/alexsuslin/gh-project-scaffold/releases/tag/v0.3.3)
  at `c103f46`. Main and tag CI and the release workflow passed.
- Implemented: doctor text/JSON reports; offline additive adoption; provenance manifest;
  existing guidance/context preservation; shared handoff template; Python starter guidance.
- Verified: CLI behavior on disposable repositories/worktrees, existing generator tests,
  package build/install, static checks and release archive smoke test (details below).
- Release delivery: [v0.3.0](https://github.com/alexsuslin/gh-project-scaffold/releases/tag/v0.3.0)
  was published on 2026-11-11.
- Verified published archive: `dist/v0.3.1-published/`.
- Verified v0.3.2 archive: `dist/v0.3.2-published/`.
- Verified v0.3.3 archive: `dist/v0.3.3-published/`.
- v0.3.4 release candidate archive: `dist/v0.3.4/`.
- Pilot follow-up: notion-cli exposed a missing Mypy candidate and busybar-ai-progress
  exposed a missing Pyright candidate. Doctor now detects both via pyproject.toml.
  Mypy delegates to configured targets or proposes the repository root as a fallback.
  The follow-up was pushed as `0aa2d0d` and passed main CI on Windows and Ubuntu
  with Python 3.11 and 3.14.
- KidPic follow-up: `50f6b7a` added discovery for the root web build script and
  executable test projects. Main CI passed on Windows and Ubuntu with Python 3.11
  and 3.14. The change was published in v0.3.2.
- Erase Garden follow-up: `bc89419` added discovery for the check script in both
  supported Godot layouts. Main CI passed on Windows and Ubuntu with Python 3.11
  and 3.14. The change was published in v0.3.3.
- Jev Advisor follow-up: `aafeb4d` added recognition of the documented npm command
  in doctor and adopt previews. Main CI passed on Windows and Ubuntu with Python
  3.11 and 3.14. The owner authorized releasing this change as v0.3.4.

## Evidence

| Revision or working state | Check / environment | Result | Evidence |
| --- | --- | --- | --- |
| v0.3.4 release candidate | Full pytest, Windows Python 3.14 | 87 passed, 1 skipped | Symlink creation unavailable. Used a short temporary path and process-scoped Git long-path support. |
| v0.3.4 release candidate | Lockfile, Ruff, Mypy and local archive | Passed | `uv lock --check --offline`. Archive matched SHA256SUMS and extracted doctor reported the README npm candidate. |
| README npm discovery | Readiness suite, Windows Python 3.14 | 38 passed, 1 skipped | `tmp-test-runs/doctor-npm-readme-green`. Fenced and inline commands, fallback and preview passed. Symlink creation unavailable. |
| README npm discovery | Ruff lint/format and mypy | Passed | Repository quality checks. |
| v0.3.3 release candidate | Full pytest, Windows Python 3.14 | 81 passed, 1 skipped | Symlink creation unavailable. Used a short temporary path and process-scoped Git long-path support. |
| v0.3.3 release candidate | Lockfile, Ruff, Mypy and local archive | Passed | `uv lock --check --offline`. Archive matched SHA256SUMS and extracted doctor reported the Godot check candidate. |
| Godot discovery working changes | Readiness suite, Windows Python 3.14 | 32 passed, 1 skipped | `tmp-test-runs/doctor-godot-green`. Both marker layouts, invalid candidates and read-only behavior passed. Symlink creation unavailable. |
| Godot discovery working changes | Ruff lint/format and mypy | Passed | Repository quality checks. |
| v0.3.2 release candidate | Full pytest, Windows Python 3.14 | 77 passed, 1 skipped | Symlink creation unavailable. Used a short temporary path and process-scoped Git long-path support. |
| v0.3.2 release candidate | Lockfile, Ruff, Mypy and local archive | Passed | `uv lock --check --offline`. Archive matched SHA256SUMS and extracted doctor reported both .NET candidates. |
| KidPic discovery working changes | Readiness suite, Windows Python 3.14 | 28 passed, 1 skipped | `tmp-test-runs/doctor-dotnet-green`. KidPic-shaped and ambiguous .NET fixtures passed. Symlink creation unavailable. |
| KidPic discovery working changes | Ruff lint/format and mypy | Passed | Repository quality checks. |
| v0.3.1 release candidate | Full pytest, Windows Python 3.14 | 75 passed, 1 skipped | Symlink creation unavailable. Used a short temporary path and process-scoped Git long-path support. |
| v0.3.1 release candidate | Lockfile, Ruff, Mypy and local archive | Passed | `uv lock --check --offline`. Archive SHA-256 matched SHA256SUMS. Extracted doctor detected both type checkers with site-packages disabled. |
| Doctor type checker discovery | Full pytest suite, Windows Python 3.14 | 75 passed, 1 skipped | Both pilot fixtures and the targetless Mypy case passed. Symlink creation was unavailable. The full run used a short temporary path and process-scoped Git long-path support. |
| Doctor type checker discovery | Ruff lint/format and mypy | Passed | python -m ruff check .; python -m ruff format --check .; python -m mypy github-project-ops/scripts scripts |
| 0.3.0 working changes | Full pytest suite, Windows Python 3.14, outside sandbox | 71 passed, 1 skipped | tmp-test-runs/full-02; the skip is unavailable symlink creation; Windows junction test passed |
| Later handoff-link/legacy-guidance refinement | Readiness pytest suite, sandbox | 22 passed, 2 skipped | tmp-test-runs/readiness-06; symlink and junction creation unavailable inside sandbox |
| 0.3.0 working changes | Ruff lint/format and mypy | Passed | python -m ruff check .; python -m ruff format --check .; python -m mypy github-project-ops/scripts scripts |
| 0.3.0 metadata | Lockfile consistency | Passed | uv lock --check --offline |
| 0.3.0 archive | SHA-256 and extracted CLI without site-packages | Passed | tmp-test-runs/release-smoke-01; doctor/adopt and shared handoff resource |
| 0.3.0 scripts | Parse with Python 3.11 syntax rules | Passed | ast.parse(feature_version=(3, 11)); not a Python 3.11 runtime test |

The first full run inside the sandbox failed because Git could not clone temporary
local fixture repositories. The successful full rerun used ordinary host execution,
with TEMP/TMP and fixtures under tmp-test-runs/. No security settings were changed.
pytest.exe was blocked by Windows Application Control; python -m pytest worked.

## Remaining work

- No known implementation blocker. Detection is intentionally shallow; commands are
  unverified candidates. Doctor does not assess the semantic freshness of handoff prose.
- Adoption records provenance only; Copier update support for adopted repositories
  is not implemented. Existing instructions are preserved rather than edited to add links.
- Next action: verify main CI and the published v0.3.4 assets after pushing the signed tag.
