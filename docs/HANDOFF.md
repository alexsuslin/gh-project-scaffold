# Handoff

Current continuation point for the 0.3.0 project-readiness release. Command contracts
and limitations are documented in [the readiness guide](../github-project-ops/references/readiness.md).

## Outcome and acceptance

- Current goal: release doctor, additive adopt, project AGENTS.md and handoff as v0.3.0.
- Acceptance: read-only diagnosis; preview without changes; preserve existing files and
  Git index; repeat adoption without rewriting edits; support existing context;
  reject unsafe paths; preserve create/update behavior and distribution builds.
- Scope: only this repository. Other personal projects and installed skills are untouched.

## Current state

- Last substantive update: 2026-11-11.
- Release identity: v0.3.0. Resolve the release tag to identify the exact source revision.
- Implemented: doctor text/JSON reports; offline additive adoption; provenance manifest;
  existing guidance/context preservation; shared handoff template; Python starter guidance.
- Verified: CLI behavior on disposable repositories/worktrees, existing generator tests,
  package build/install, static checks and release archive smoke test (details below).
- Delivery: the owner authorized a commit, push to main and publication on 2026-11-11.
  The [GitHub release](https://github.com/alexsuslin/gh-project-scaffold/releases/tag/v0.3.0)
  and [release workflow](https://github.com/alexsuslin/gh-project-scaffold/actions/workflows/release.yml)
  are authoritative for remote publication and its checks; this document is prepared before publication.
- Local artifact: dist/v0.3.0/github-project-ops-v0.3.0.zip and SHA256SUMS.
- User scenario: adopted this repository, then customized its AGENTS.md and this handoff.
  No adoption or deployment was performed in any other personal project.

## Evidence

| Revision or working state | Check / environment | Result | Evidence |
| --- | --- | --- | --- |
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
- Release acceptance: main contains the implementation, signed v0.3.0 identifies the
  intended source, CI and the release workflow pass, and the published ZIP matches SHA256SUMS.
- Next concrete action after release: select a pilot repository only when the owner
  includes it in a new task. Existing projects remain outside this release's scope.
- Who can take it: owner or a session with that explicit project scope.
