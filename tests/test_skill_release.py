from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_release.py"


def make_release_repository(tmp_path: Path) -> Path:
    assert BUILD_SCRIPT.is_file(), "release builder has not been implemented"

    repository = tmp_path / "repository"
    (repository / "scripts").mkdir(parents=True)
    (repository / "github-project-ops" / "references").mkdir(parents=True)
    (repository / "github-project-ops" / "assets" / ".ruff_cache").mkdir(parents=True)
    (repository / "github-project-ops" / ".venv").mkdir(parents=True)

    shutil.copy2(BUILD_SCRIPT, repository / "scripts" / "build_release.py")
    (repository / "VERSION").write_bytes(b"0.2.0\n")
    (repository / "LICENSE").write_bytes(b"MIT license fixture\n")
    (repository / "copier.yml").write_text(
        "_subdirectory: github-project-ops/assets/templates\n", encoding="utf-8"
    )
    (repository / "github-project-ops" / "SKILL.md").write_text(
        "# Skill fixture\n", encoding="utf-8"
    )
    (repository / "github-project-ops" / "references" / "guide.md").write_text(
        "Release guide fixture\n", encoding="utf-8"
    )
    (repository / "github-project-ops" / "assets" / ".ruff_cache" / "cache.bin").write_bytes(
        b"cache"
    )
    (repository / "github-project-ops" / ".venv" / "installed.py").write_text(
        "ignored = True\n", encoding="utf-8"
    )
    (repository / "github-project-ops" / "generated.pyc").write_bytes(b"bytecode")
    return repository


def run_builder(
    repository: Path, output_directory: Path, tag: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(repository / "scripts" / "build_release.py"),
            "--tag",
            tag,
            "--output-dir",
            str(output_directory),
        ],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )


def test_builds_expected_archive_inventory_and_excludes_generated_files(tmp_path: Path) -> None:
    repository = make_release_repository(tmp_path)
    skill = repository / "github-project-ops"
    symlink = skill / "references" / "linked.md"
    try:
        os.symlink(skill / "SKILL.md", symlink)
    except OSError:
        symlink = None

    output = tmp_path / "release"
    result = run_builder(repository, output, "v0.2.0")

    assert result.returncode == 0, result.stdout + result.stderr
    archive = output / "github-project-ops-v0.2.0.zip"
    with zipfile.ZipFile(archive) as built:
        assert built.namelist() == [
            "LICENSE",
            "VERSION",
            "copier.yml",
            "github-project-ops/LICENSE",
            "github-project-ops/SKILL.md",
            "github-project-ops/references/guide.md",
        ]
        assert built.read("VERSION") == b"0.2.0\n"
        assert built.read("github-project-ops/LICENSE") == b"MIT license fixture\n"
        if symlink is not None:
            assert "github-project-ops/references/linked.md" not in built.namelist()


def test_repeated_builds_have_identical_bytes_and_checksum(tmp_path: Path) -> None:
    repository = make_release_repository(tmp_path)
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    first_result = run_builder(repository, first_output, "v0.2.0")
    assert first_result.returncode == 0, first_result.stdout + first_result.stderr

    skill_file = repository / "github-project-ops" / "SKILL.md"
    os.utime(skill_file, (2_000_000_000, 2_000_000_000))
    second_result = run_builder(repository, second_output, "v0.2.0")
    assert second_result.returncode == 0, second_result.stdout + second_result.stderr

    archive_name = "github-project-ops-v0.2.0.zip"
    first_archive = (first_output / archive_name).read_bytes()
    second_archive = (second_output / archive_name).read_bytes()
    assert first_archive == second_archive

    digest = hashlib.sha256(first_archive).hexdigest()
    expected_checksum = f"{digest}  {archive_name}\n"
    assert (first_output / "SHA256SUMS").read_text(encoding="utf-8") == expected_checksum
    assert (second_output / "SHA256SUMS").read_text(encoding="utf-8") == expected_checksum


@pytest.mark.parametrize("tag", ["v0.2.1", "0.2.0", "v0.2.0-rc.1"])
def test_rejects_tag_that_does_not_exactly_match_stable_version(tmp_path: Path, tag: str) -> None:
    repository = make_release_repository(tmp_path)
    output = tmp_path / "release"

    result = run_builder(repository, output, tag)

    assert result.returncode == 2
    assert "v0.2.0" in result.stderr
    assert not output.exists()


def test_rejects_output_directory_inside_skill_before_writing(tmp_path: Path) -> None:
    repository = make_release_repository(tmp_path)
    output = repository / "github-project-ops" / "dist"

    result = run_builder(repository, output, "v0.2.0")

    assert result.returncode == 2
    assert "inside" in result.stderr
    assert not output.exists()
