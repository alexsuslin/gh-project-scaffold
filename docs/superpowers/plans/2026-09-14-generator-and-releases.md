# Generator and Releases Implementation Plan

Goal: generate previewable Python projects, update them with Copier, license the
repository under MIT, and publish versioned skill archives through GitHub Releases.

Architecture: use Copier 9.18.2 for rendering and three-way updates. A small
standalone CLI owns validation, preview isolation, and exit codes. Existing
template assets remain the single template source; rendered project tests cover them.
Publication has a read-only verification/build job and a separate release job.

User decisions: MIT; GitHub Releases archives only. Git/YubiKey settings are
diagnosed and documented, not changed by this work.

1. Generator and template:
   - Convert variable-bearing assets to Jinja and add copier.yml plus answer recording.
   - Add create DEST --name NAME --owner OWNER [--preview] [--source SOURCE] [--ref REF].
   - Render into temporary storage first. Preview emits unified diffs. Creation
     refuses an existing nonempty target and writes only after successful rendering.
   - Test name/path validation, no preview writes, public/private projects,
     rendered metadata, module imports, and distribution builds.
2. Updates:
   - Add update DEST [--preview] [--ref REF].
   - Require a clean Git repository and recorded Copier answers.
   - Run preview in an isolated Git clone. Report diffs and conflicts.
   - Real updates use Copier's merge behavior and return nonzero on conflicts.
   - Test two committed template revisions, preserved user changes, conflicts,
     deleted files, dirty repositories, and preview immutability.
3. Licensing and archives:
   - Install the complete MIT license and fix the truncated license asset.
   - Add a deterministic zip builder with license, skill files, version metadata,
     checksum, and explicit exclusions for caches.
   - Add tagged-release automation. Validate version, test, build, then upload
     assets into a GitHub Release with job-scoped contents: write.
4. Documentation and verification:
   - Document commands, update requirements, conflict recovery, release procedure,
     and YubiKey agent workflow.
   - Run tests, Ruff, mypy, actual generated-project checks, and independent review.
   - Preserve required commit signing; do not publish until a signed commit and
     intended release tag exist.