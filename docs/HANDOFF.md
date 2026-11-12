# Handoff

Current continuation point after the 0.3.0 project-readiness pilots. Command contracts
and limitations are documented in [the readiness guide](../github-project-ops/references/readiness.md).

## Outcome and acceptance

- v0.3.6 is published and the defi-trader pilot is complete.
- Acceptance met: installed doctor finds the Paper Lab command, adoption is in
  GitHub `main`, and the offline suite passed on the adoption commit.
- Current follow-up verifies that doctor recommends building before browser
  tests when an npm project's README documents that order.

## Current state

- Last substantive update: 2026-11-12.
- Published baseline: [v0.3.6](https://github.com/alexsuslin/gh-project-scaffold/releases/tag/v0.3.6)
  at `62ee5ac`. GitHub verified the signed tag. Main and tag CI and the release workflow passed.
- Implemented: doctor text/JSON reports; offline additive adoption; provenance manifest;
  existing guidance/context preservation; shared handoff template; Python starter guidance.
- Verified: CLI behavior on disposable repositories/worktrees, existing generator tests,
  package build/install, static checks and release archive smoke test (details below).
- Release delivery: [v0.3.0](https://github.com/alexsuslin/gh-project-scaffold/releases/tag/v0.3.0)
  was published on 2026-11-11.
- Verified published archive: `dist/v0.3.1-published/`.
- Verified v0.3.2 archive: `dist/v0.3.2-published/`.
- Verified v0.3.3 archive: `dist/v0.3.3-published/`.
- Verified v0.3.4 archive: `dist/v0.3.4-published/`.
- Verified v0.3.5 archive: `dist/v0.3.5-published/`.
- Verified v0.3.6 archive: `dist/v0.3.6-published/`. The ZIP matched `SHA256SUMS`.
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
  3.11 and 3.14. The change was published in v0.3.4.
- Teo-tales follow-up: `afa0a19` added recognition of the documented Mypy command
  in doctor and adopt previews. Main CI passed on Windows and Ubuntu with Python
  3.11 and 3.14. The change was published in v0.3.5.
- Paper Lab follow-up: `302a65c` added recognition of the README's PowerShell
  setup and `unittest discover -s tests -q`. Installed doctor v0.3.6 found it in
  defi-trader and reported it as a candidate.
- defi-trader pilot: the signed adoption commit `0355d8cf` landed in GitHub `main`
  with `.scaffold.json`, `docs/HANDOFF.md`, and a handoff link in `AGENTS.md`.
  Signed follow-up `d5d7f0ab` recorded the offline test results in that handoff.
- hellisus-cheatsheet pilot: signed adoption commit `a3a461a` documented the build
  prerequisite in `AGENTS.md`. The Pages workflow passed through browser tests
  and deployment. [Workflow run](https://github.com/alexsuslin/hellisus-cheatsheet/actions/runs/43222800020)
- Doctor now reports the README's `npm run build && npm run test:browser` sequence
  as an unverified candidate when both npm scripts are defined.

## Evidence

| Revision or working state | Check / environment | Result | Evidence |
| --- | --- | --- | --- |
| npm browser test discovery | Readiness suite on Windows | 51 passed, 2 skipped | Synthetic repositories covered the commented command list, inline chain, and fallback cases. Junction and symlink creation were unavailable. Ruff and mypy passed. |
| defi-trader `0355d8cf` | `unittest discover -s tests -q` in a separate clone, Windows Python 3.13.15 | 358 passed, 2 symlink checks skipped | Used a fresh `.venv-paper` from both lockfiles. Result recorded in `d5d7f0ab`. |
| v0.3.6 release candidate | Full pytest, Windows Python 3.14 | 94 passed, 1 skipped | Symlink creation unavailable. Used a short temporary path and process-scoped Git long-path support. |
| v0.3.6 release candidate | Lockfile, Ruff, Mypy and local archive | Passed | `uv lock --check --offline`. Archive matched SHA256SUMS and extracted doctor reported the Paper Lab offline check. |
| README Paper Lab discovery | Readiness suite, Windows Python 3.14 | 45 passed, 1 skipped | `tmp-test-runs/doctor-paper-lab-green`. Exact match, partial matches, fallback, preview and prior README candidates checked. Symlink creation unavailable. |
| README Paper Lab discovery | Ruff lint/format and mypy | Passed | Repository quality checks. |
| v0.3.5 release candidate | Full pytest, Windows Python 3.14 | 90 passed, 1 skipped | Symlink creation unavailable. Used a short temporary path and process-scoped Git long-path support. |
| v0.3.5 release candidate | Lockfile, Ruff, Mypy and local archive | Passed | `uv lock --check --offline`. Archive matched SHA256SUMS and extracted doctor reported the documented Mypy command. |
| README Mypy discovery | Readiness suite, Windows Python 3.14 | 41 passed, 1 skipped | `tmp-test-runs/doctor-mypy-readme-green`. Teo-tales layout, fallback, preview and npm regressions passed. Symlink creation unavailable. |
| README Mypy discovery | Ruff lint/format and mypy | Passed | Repository quality checks. |
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
- Next action: review and commit the browser test discovery changes when authorized.
