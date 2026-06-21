# GitHub Actions

## GitHub Actions Baseline

Use GitHub Actions for the minimum automation needed to keep the repository healthy without burying the project in workflow noise.

## CI

- Run tests on pushes and pull requests.
- Run linting and type checks when the repository has them.
- Keep the default CI path fast enough that contributors can trust it.

## Release

- Use a dedicated release workflow for tags, release branches, or manual dispatch.
- Build artifacts in the workflow that owns the release so tags and outputs stay aligned.
- Avoid publishing side effects from ordinary CI jobs.

## Artifacts

- Upload build outputs as artifacts when they help review or release confidence.
- Keep artifact names predictable and tied to version or platform.
- Retain only what is useful; avoid bloating releases with redundant bundles.

## Publish

- Publish only when the project needs distribution automation.
- Separate "build and verify" from "publish" when credentials or trust boundaries matter.
- For Python projects, prefer building wheels and source distributions before any publication step.

## Minimal vs Extended Workflows

- Start with one `ci.yml` and one `release.yml`.
- Add matrix builds, caching, or publish jobs only when the project benefits from them.
- Preserve an existing coherent workflow if it already meets the repository's needs.
