from __future__ import annotations

import argparse
import json
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

BASE_REQUIRED_PATHS = ["README.md", "pyproject.toml", ".github/workflows/ci.yml"]
PUBLIC_REQUIRED_PATHS = ["CONTRIBUTING.md", "SECURITY.md"]


@dataclass
class ValidationReport:
    root: str
    stack: str
    public: bool
    missing: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.errors


def collect_missing(root: Path, required_paths: list[str]) -> list[str]:
    return [item for item in required_paths if not (root / item).is_file()]


def validate_scaffold(root: Path, *, stack: str, public: bool) -> ValidationReport:
    report = ValidationReport(root=str(root), stack=stack, public=public)
    required = list(BASE_REQUIRED_PATHS)
    if stack == "generic":
        required.remove("pyproject.toml")
    if public:
        required.extend(PUBLIC_REQUIRED_PATHS)

    # GitHub accepts both extensions. Prefer the original name when both exist.
    if (
        not (root / ".github/workflows/ci.yml").is_file()
        and (root / ".github/workflows/ci.yaml").is_file()
    ):
        required[required.index(".github/workflows/ci.yml")] = ".github/workflows/ci.yaml"

    report.missing = collect_missing(root, required)
    for relative_path in required:
        if relative_path in report.missing:
            continue
        try:
            content = (root / relative_path).read_text(encoding="utf-8-sig")
            if not content.strip():
                report.errors.append(f"{relative_path}: file is empty")
            elif relative_path == "pyproject.toml":
                tomllib.loads(content)
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            report.errors.append(f"{relative_path}: {error}")
    return report


def print_report(report: ValidationReport, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": report.ok, **asdict(report)}, ensure_ascii=True))
    elif report.ok:
        print("Scaffold looks complete.")
    else:
        if report.missing:
            print(f"Missing required paths: {report.missing}")
        for error in report.errors:
            print(f"Error: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate scaffold files (Python 3.11+, no third-party dependencies)."
    )
    parser.add_argument("repo_path", help="Path to the generated repository scaffold")
    parser.add_argument(
        "--public",
        action="store_true",
        help="Require public-facing contributor and security docs",
    )
    parser.add_argument(
        "--stack",
        choices=("python", "generic"),
        default="python",
        help="Use generic to skip Python metadata checks (default: python)",
    )
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON report")
    args = parser.parse_args()

    # Invalid roots are invocation errors; incomplete scaffolds are validation failures.
    root = Path(args.repo_path)
    try:
        root = root.resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {root}")
    except (OSError, RuntimeError, ValueError) as error:
        report = ValidationReport(str(root), args.stack, args.public, errors=[str(error)])
        print_report(report, as_json=args.json)
        return 2

    try:
        report = validate_scaffold(root, stack=args.stack, public=args.public)
    except OSError as error:
        report = ValidationReport(str(root), args.stack, args.public, errors=[str(error)])
    print_report(report, as_json=args.json)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
