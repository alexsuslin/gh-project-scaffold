# Research and implementation decisions

Reviewed 2026-09-14; implementation extended 2026-09-15 and 2026-11-11.

| Project | Useful idea | Applied here |
| --- | --- | --- |
| [Scientific Python cookie](https://github.com/scientific-python/cookie) | Test the generated project, not only template inventory. | Tests render the template, build sdist/wheel, install the wheel, and import it in isolation. |
| [Hypermodern Python Cookiecutter](https://github.com/cjolowicz/cookiecutter-hypermodern-python) | Integrated quality checks and dependency automation. | pytest, Ruff, mypy, CI, and Dependabot; one coherent Python toolchain. |
| [Copier](https://github.com/copier-org/copier) | Saved answers, template revisions, and three-way updates. | Uses Copier directly for rendering and merge computation, with an isolated preview and local-file collision checks. |

## Why a small wrapper around Copier?

Copier owns rendering, old/new template reconstruction, and merge computation.
The wrapper provides a predictable noninteractive CLI, unified diffs, and a
conservative application step. It computes updates in a clone, refuses conflicts
and collisions with ignored files, and applies only the reviewed paths. It does
not implement a second merge algorithm.

The original scaffold validator accepted empty files/directories and rejected
ci.yaml. Those issues are covered by regression tests. The original Python
sample could not build a wheel because it lacked a package; the generated
project is now exercised through a real build and install.

The initial license asset contained only part of the MIT text. It has been
completed, and the user selected MIT for this repository. Releases distribute
the skill with its license and version.

## Explicit scope

Implemented: parameterized Python generation, diff previews, saved answers,
Copier updates, MIT licensing, deterministic archive creation, and tag-triggered
GitHub Release automation.

Version 0.3 adds read-only doctor, additive adoption with provenance, concrete
agent entry points and one handoff document. Existing projects keep their stack,
instructions and context; adoption is not a Copier migration. These choices address
the need to continue work in established repositories without duplicating their docs.

Not included: Copier migration/update of unrelated existing repositories, PyPI
publication, additional language generators, or unattended use of the user's
hardware signing key. Symbolic links and file/directory transitions can require
manual handling. These are boundaries, not hidden partial implementations.

Future work should be driven by actual projects: additional discovery profiles,
explicit update policies for adopted files, native Copier answer changes exposed
in the wrapper, or additional publishing targets. No other projects are changed
as part of the 0.3 implementation.
