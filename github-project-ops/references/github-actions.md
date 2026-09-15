# GitHub Actions

## CI

The bundled Python CI installs the package, runs pytest, checks Ruff formatting
and lint, runs mypy, and builds distributions. Its Linux/Windows matrix covers
Python 3.11 and 3.14. Adapt the matrix to the project's actual support policy.

Use explicit `contents: read` permissions and disable persisted checkout
credentials when subsequent steps do not need Git authentication.
Pin third-party actions to reviewed commit SHAs with a version comment.
Keep pins current through Dependabot; check runner requirements when upgrading
action major versions, especially for self-hosted runners.

Cancel superseded CI runs with a workflow/ref concurrency group. Keep job
timeouts finite and use caches tied to the dependency manifest.

## Release artifacts

The bundled `release.yml` runs on `v*` tags or manual dispatch. It validates
tag/version agreement for tagged runs, reruns tests and quality checks, builds
wheel/sdist files, and uploads workflow artifacts. Artifact names include the
commit SHA; missing artifacts fail the job.

The tag check uses the static `[project].version` from the bundled template.
For a project with dynamic/VCS versioning, adapt that check to the existing
version source.

A successful artifact build is not a published release. This template does not
create GitHub Releases or publish packages. Keep release runs independent of
CI cancellation so a newer push cannot cancel an in-flight release build.

## Optional publishing

Add publishing when distribution is part of the user's request. Keep build and
publish jobs separate. For PyPI, prefer Trusted Publishing with OIDC and a
configured GitHub environment over long-lived API tokens. Grant
`id-token: write` only to the publishing job. GitHub Release creation similarly
needs `contents: write` only in its release job.

Configure the destination project/environment before claiming publishing works.
Avoid publishing from pull-request or ordinary test jobs.

## Maintenance

The bundled Dependabot file updates Python requirements and workflow actions.
The skill repository's root Dependabot additionally updates its uv development
lockfile. Update template Python dependencies manually because the source manifest is Jinja. GitHub's Actions updater scans root
workflows, so maintainers must propagate reviewed action updates into the bundled
templates too.