"""Verify a release bundle built by ``scripts/build_release.py``.

Prints a JSON summary and exits 1 when any check fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_release import (  # noqa: E402
    ARTIFACT_FILES,
    DASHBOARD_GLOBS,
    DOC_FILES,
    ROOT_FILES,
    SCREENSHOT_GLOB,
    read_checksums,
    sha256_file,
)


def verify_release(root: Path) -> dict:
    root = Path(root)
    errors: list[str] = []
    checksums_verified = 0

    if not root.is_dir():
        return {
            "ok": False,
            "root": str(root),
            "files": 0,
            "checksums_verified": 0,
            "errors": [f"release directory does not exist: {root}"],
        }

    files = {path.relative_to(root) for path in root.rglob("*") if path.is_file()}

    sums_path = root / "SHA256SUMS"
    if not sums_path.is_file():
        errors.append(f"missing SHA256SUMS: {sums_path}")
    else:
        try:
            entries = read_checksums(sums_path)
        except (OSError, ValueError) as error:
            errors.append(str(error))
        else:
            listed: set[Path] = set()
            for name, expected in entries:
                relative = Path(name)
                listed.add(relative)
                target = root / relative
                if not target.is_file():
                    errors.append(f"file listed in SHA256SUMS is missing: {target}")
                    continue
                actual = sha256_file(target)
                if actual != expected:
                    errors.append(
                        f"SHA256SUMS mismatch for {target}: expected {expected}, got {actual}"
                    )
                else:
                    checksums_verified += 1
            for extra in sorted(files - listed - {Path("SHA256SUMS")}):
                errors.append(f"file is not listed in SHA256SUMS: {root / extra}")

    required = [*ROOT_FILES, "RELEASE_NOTES.md", "SHA256SUMS", *DOC_FILES]
    required += [f"artifacts/{name}" for name in ARTIFACT_FILES]
    for name in required:
        if not (root / name).is_file():
            errors.append(f"missing required file: {root / name}")

    dashboard_dir = root / "dashboard"
    if not any(path for pattern in DASHBOARD_GLOBS for path in dashboard_dir.glob(pattern)):
        errors.append(f"missing dashboard Power BI file (*.pbix or *.pbip): {dashboard_dir}")
    if not any(dashboard_dir.glob(SCREENSHOT_GLOB)):
        errors.append(f"missing dashboard screenshot (screenshots/*.png): {dashboard_dir}")

    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts[:2] == ("data", "raw"):
            errors.append(f"raw data is not allowed in the bundle: {path}")
        if path.is_file() and (path.name == ".env" or path.name.startswith(".env.")):
            errors.append(f"environment file is not allowed in the bundle: {path}")

    return {
        "ok": not errors,
        "root": str(root),
        "files": len(files),
        "checksums_verified": checksums_verified,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify_release")
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = verify_release(args.root)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
