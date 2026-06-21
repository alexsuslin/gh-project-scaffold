from __future__ import annotations

import argparse
from pathlib import Path


BASE_REQUIRED_PATHS = [
    "README.md",
    "pyproject.toml",
    ".github/workflows/ci.yml",
]

PUBLIC_REQUIRED_PATHS = [
    "CONTRIBUTING.md",
    "SECURITY.md",
]


def collect_missing(root: Path, required_paths: list[str]) -> list[str]:
    return [item for item in required_paths if not (root / item).exists()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the minimum scaffold created by github-project-ops."
    )
    parser.add_argument("repo_path", help="Path to the generated repository scaffold")
    parser.add_argument(
        "--public",
        action="store_true",
        help="Require public-facing contributor and security docs",
    )
    args = parser.parse_args()

    root = Path(args.repo_path).resolve()
    required = list(BASE_REQUIRED_PATHS)
    if args.public:
        required.extend(PUBLIC_REQUIRED_PATHS)

    missing = collect_missing(root, required)
    if missing:
        print(f"Missing required paths: {missing}")
        return 1

    print("Scaffold looks complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
