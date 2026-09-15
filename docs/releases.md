# Skill releases

Releases publish the Codex skill as a deterministic ZIP archive on GitHub. They
do not publish a Python package or upload anything to PyPI.

## Build locally

`VERSION` is the release source of truth and must contain a stable SemVer value
such as `0.2.0`. The tag passed to the builder must be that version prefixed
with `v`.

```sh
uv run --locked python scripts/build_release.py --tag v0.2.0 --output-dir dist
```

The command creates:

- `dist/github-project-ops-v0.2.0.zip`
- `dist/SHA256SUMS`

The ZIP contains the repository `LICENSE`, `VERSION`, and `copier.yml`, plus
the installable `github-project-ops/` skill tree. The MIT license is also
stored at `github-project-ops/LICENSE`, so it remains with a copied skill.
Cache directories, `.venv`, Python bytecode, and symbolic links are omitted.
File order, timestamps, permissions, and compression settings are fixed so
repeated builds from identical bytes produce the same archive and checksum.

The output directory must be outside `github-project-ops/`. The builder checks
the version, tag, required inputs, and output path before creating output files.

Verify the checksum on Linux:

```sh
cd dist
sha256sum --check SHA256SUMS
```

On macOS, use shasum instead:

```sh
cd dist
shasum -a 256 --check SHA256SUMS
```

Verify it in PowerShell:

```powershell
$expected = (Get-Content .\dist\SHA256SUMS).Split()[0]
$actual = (Get-FileHash .\dist\github-project-ops-v0.2.0.zip -Algorithm SHA256).Hash.ToLower()
if ($actual -ne $expected) { throw "Release checksum mismatch" }
```

## Publish a release

Before tagging, run the locked test, formatting, lint, and type-check commands
from the development guide. Update `VERSION` in the commit intended for the
release, create the repository's required signed tag for that exact commit, and
push the tag:

```sh
git tag -s v0.2.0
git push origin v0.2.0
```

A pushed `v*` tag starts `.github/workflows/release.yml`. The build job checks
that the requested tag resolves to the checked-out commit, installs locked
dependencies, runs pytest, Ruff, and mypy, builds the archive, and passes only
the ZIP and checksum to the publish job. The publish job alone receives
`contents: write` permission and creates the GitHub Release with
`gh release create --verify-tag`.

The workflow can also be started manually with an existing tag through
`workflow_dispatch`. Enter the complete tag, such as `v0.2.0`; the same commit
and version checks apply.

Published releases are immutable in this workflow. If a GitHub Release already
exists for the tag, the publish job fails instead of replacing its assets.
Correct a release with a new version and tag.
