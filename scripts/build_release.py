from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import zipfile
from collections.abc import Sequence
from pathlib import Path

SKILL_DIRECTORY = "github-project-ops"
ROOT_RELEASE_FILES = ("LICENSE", "VERSION", "copier.yml")
EXCLUDED_DIRECTORIES = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
STABLE_SEMVER = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class ReleaseBuildError(ValueError):
    """A release request that is unsafe or inconsistent with the repository."""


def _read_version(repository: Path) -> str:
    version_path = repository / "VERSION"
    if version_path.is_symlink() or not version_path.is_file():
        raise ReleaseBuildError("VERSION must be a regular file")

    version = version_path.read_text(encoding="utf-8").strip()
    if STABLE_SEMVER.fullmatch(version) is None:
        raise ReleaseBuildError(f"VERSION must contain a stable SemVer value, got {version!r}")
    return version


def _validate_request(repository: Path, output_directory: Path, tag: str) -> str:
    repository = repository.resolve()
    skill_directory = (repository / SKILL_DIRECTORY).resolve()
    if not skill_directory.is_dir():
        raise ReleaseBuildError(f"missing skill directory: {skill_directory}")

    output_directory = output_directory.resolve()
    if output_directory == skill_directory or skill_directory in output_directory.parents:
        raise ReleaseBuildError("output directory cannot be inside the skill directory")

    version = _read_version(repository)
    expected_tag = f"v{version}"
    if tag != expected_tag:
        raise ReleaseBuildError(f"release tag must be {expected_tag}, got {tag!r}")

    return version


def _release_entries(repository: Path) -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []

    for filename in ROOT_RELEASE_FILES:
        source = repository / filename
        if source.is_symlink() or not source.is_file():
            raise ReleaseBuildError(f"{filename} must be a regular file")
        contents = source.read_bytes()
        entries.append((filename, contents))
        if filename == "LICENSE":
            entries.append((f"{SKILL_DIRECTORY}/LICENSE", contents))

    skill_directory = repository / SKILL_DIRECTORY
    for source in skill_directory.rglob("*"):
        relative = source.relative_to(skill_directory)
        if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if source.suffix == ".pyc" or source.is_symlink() or not source.is_file():
            continue

        archive_path = (Path(SKILL_DIRECTORY) / relative).as_posix()
        if archive_path == f"{SKILL_DIRECTORY}/LICENSE":
            continue
        entries.append((archive_path, source.read_bytes()))

    return sorted(entries, key=lambda entry: entry[0])


def _archive_bytes(entries: Sequence[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for archive_path, contents in entries:
            metadata = zipfile.ZipInfo(archive_path, date_time=ZIP_TIMESTAMP)
            metadata.compress_type = zipfile.ZIP_DEFLATED
            metadata.create_system = 3
            metadata.external_attr = 0o100644 << 16
            archive.writestr(metadata, contents, compresslevel=9)
    return buffer.getvalue()


def build_release(repository: Path, output_directory: Path, tag: str) -> tuple[Path, Path]:
    """Build a deterministic skill archive and its SHA-256 manifest."""
    repository = repository.resolve()
    output_directory = output_directory.resolve()

    _validate_request(repository, output_directory, tag)
    entries = _release_entries(repository)
    archive_bytes = _archive_bytes(entries)

    archive_name = f"{SKILL_DIRECTORY}-{tag}.zip"
    digest = hashlib.sha256(archive_bytes).hexdigest()
    checksum_contents = f"{digest}  {archive_name}\n"

    output_directory.mkdir(parents=True, exist_ok=True)
    archive_path = output_directory / archive_name
    checksum_path = output_directory / "SHA256SUMS"
    archive_path.write_bytes(archive_bytes)
    checksum_path.write_text(checksum_contents, encoding="utf-8", newline="\n")
    return archive_path, checksum_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a deterministic skill release archive.")
    parser.add_argument("--tag", required=True, help="Release tag; must exactly match vVERSION")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Directory for the archive and SHA256SUMS (default: dist)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    repository = Path(__file__).resolve().parents[1]

    try:
        archive_path, checksum_path = build_release(
            repository,
            arguments.output_dir,
            arguments.tag,
        )
    except (OSError, ReleaseBuildError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(archive_path)
    print(checksum_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
