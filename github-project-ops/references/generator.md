# Generate and update projects

The generator requires Git and Python 3.11+. Running it with uv installs the
Copier version pinned in the script metadata. The structural validator remains
dependency-free.

## Create with a diff preview

From a checkout of this repository:

```sh
uv run github-project-ops/scripts/scaffold.py create ../weather-kit --name weather-kit --owner YOUR_GITHUB_LOGIN --preview
uv run github-project-ops/scripts/scaffold.py create ../weather-kit --name weather-kit --owner YOUR_GITHUB_LOGIN
```

From an installed skill, substitute the actual path to `scripts/scaffold.py`.
Both commands use the latest tagged version of the GitHub template by default.
For repeatable generation, add `--ref v0.2.0` once that release exists.

Options:

- `--package weather_kit`: override the Python import name.
- `--description "Weather utilities"`: project metadata and README description.
- `--visibility private`: omit public contributor/security files.
- `--license none`: omit the default MIT license.
- `--source /path/to/template-repository --ref TAG`: use a local versioned template.

Preview prints unified diffs and creates neither the destination nor its parents.
Create renders successfully before writing and requires an empty destination;
an existing `.git` directory is allowed. It does not initialize Git, commit,
install the generated project's dependencies, or publish anything.

The generated `.copier-answers.yml` records the template source, revision, and
answers. Keep it in Git. For reliable updates, use committed/tagged template
sources; a local unversioned or dirty source is not a reproducible update baseline.

After generation, install and verify the project using its README commands.

## Update a generated project

The destination must be a clean Git repository with the recorded answers
committed. Review/commit your application changes first.

```sh
uv run github-project-ops/scripts/scaffold.py update ../weather-kit --preview
uv run github-project-ops/scripts/scaffold.py update ../weather-kit
```

Add `--ref TAG` to select a particular template revision. The wrapper asks Copier
to merge the old template, the new template, and the committed project in an
isolated clone. Preview shows that diff without changing the original files,
HEAD, or index. A successful real update applies those prepared file changes;
review `git diff` and commit them yourself.

All changed paths are checked before applying. An ignored local file collision
or a symbolic-link/path-type conflict stops the operation without applying the
planned update. User-owned files outside the template are preserved. Template
file removals are included. Filesystem failures during the write phase can still
leave a partial diff; inspect it before retrying.

## Conflicts and advanced changes

Conflicting merges return exit code 3, display the conflict diff, and leave the
original project untouched. For manual resolution, use native Copier in a new
branch, with the same target revision:

```sh
git switch -c update-template
uvx --from copier==9.18.2 copier update --defaults --overwrite --skip-tasks --vcs-ref TAG
```

Native Copier writes conflict markers to the working tree. Resolve them, inspect
the diff, and run your tests before committing. Do not edit the answers file by
hand; use native Copier `--data KEY=VALUE` when changing saved answers.

The wrapper skips template tasks and does not enable unsafe extensions.
It supports ordinary file updates; symbolic links and file/directory transitions
can require manual handling. It does not migrate arbitrary existing repositories
that lack Copier's saved baseline.

Exit codes: 0 success/preview; 2 invalid input, unsafe collision, or operational
failure; 3 merge conflicts. Preview may clone/download a template and write to
temporary storage, but does not modify the requested destination.

See [Copier's update documentation](https://copier.readthedocs.io/en/stable/updating/)
for the underlying merge model.