# gh-project-scaffold

`gh-project-scaffold` is a GitHub-hosted Codex skill repository for the `github-project-ops` skill.

The skill helps Codex bootstrap and maintain software projects with Python-first, public-by-default development practices, including:

- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, and `SECURITY.md`
- GitHub Actions CI/CD workflows
- semantic versioning, changelogs, branching, tagging, and release notes
- XDG-aware runtime layout guidance for applications

## Repo Layout

```text
gh-project-scaffold/
  github-project-ops/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
  tests/
```

## Local Validation

Run the repository tests:

```powershell
pytest .\tests\test_github_project_ops_repo.py -v
```

Run the skill validator:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\github-project-ops
```

## Install Into Codex

Copy the `github-project-ops` folder into your profile skills directory:

```powershell
Copy-Item -Recurse .\github-project-ops "$env:USERPROFILE\.codex\skills\"
```

After the repo is published, the skill can also be installed from GitHub using the Codex skill installer with the repository path `github-project-ops`.
