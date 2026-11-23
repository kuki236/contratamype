"""Build a local release bundle with checksums.

The bundle never includes raw data. It is deterministic: the same inputs produce
the same SHA256SUMS (no timestamps in the manifest). Inputs are validated and
pipeline checksums are verified before the previous bundle is replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_FILES = (
    "quality_report.json",
    "run_manifest.json",
    "checksums.sha256",
    "mype_opportunities.csv",
    "tenders.parquet",
    "awards.parquet",
    "contracts.parquet",
    "buyers.parquet",
    "suppliers.parquet",
)

ROOT_FILES = (
    "README.md",
    "README.en.md",
    "LICENSE",
)

DOC_FILES = (
    "docs/data-dictionary.md",
    "docs/architecture.md",
    "docs/data-profile-2025.md",
    "docs/cohort-2025.json",
    "docs/cohort-2024.json",
    "docs/quality-checks.md",
    "docs/market-findings-2025.md",
    "docs/market-findings-2024-2025.md",
    "docs/llm-policy.md",
    "docs/llm-eval-sample-2025.json",
    "docs/llm-evaluation-v1.0.0.md",
    "docs/v1.1-plan.md",
    "docs/release.md",
    "docs/user-test-v1.0.0.md",
    "docs/web.md",
    "docs/powerbi.md",
    "docs/alerts.md",
)

DASHBOARD_GLOBS = ("*.pbix", "*.pbip")
SCREENSHOT_GLOB = "screenshots/*.png"
SHA256_HEX = re.compile(r"[0-9a-fA-F]{64}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checksums(path: Path) -> list[tuple[str, str]]:
    """Parse a ``sha256sum``-style file and return (name, digest) pairs."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"missing checksums file: {path}")
    entries: list[tuple[str, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        digest, separator, name = line.partition("  ")
        relative = Path(name)
        if (
            not separator
            or not SHA256_HEX.fullmatch(digest)
            or not name
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise ValueError(f"invalid checksum line {number} in {path}: {line!r}")
        entries.append((name, digest.lower()))
    if not entries:
        raise ValueError(f"checksums file is empty: {path}")
    return entries


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _verify_artifact_checksums(artifacts_dir: Path) -> None:
    checksums_path = artifacts_dir / "checksums.sha256"
    for name, expected in read_checksums(checksums_path):
        source = artifacts_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"file listed in checksums.sha256 is missing: {source}")
        actual = sha256_file(source)
        if actual != expected:
            raise ValueError(
                f"checksum mismatch in checksums.sha256 for {source}: "
                f"expected {expected}, got {actual}"
            )


def _verify_run_manifest(artifacts_dir: Path) -> dict:
    manifest_path = artifacts_dir / "run_manifest.json"
    manifest = _read_json(manifest_path)

    input_sha256 = manifest.get("input_sha256")
    if not isinstance(input_sha256, str) or not SHA256_HEX.fullmatch(input_sha256):
        raise ValueError(
            f"run_manifest.json input_sha256 must be 64 hex characters, got {input_sha256!r}"
        )

    hashes = manifest.get("artifacts_sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("run_manifest.json artifacts_sha256 must be a non-empty object")
    for name, expected in hashes.items():
        if (
            not isinstance(name, str)
            or not isinstance(expected, str)
            or not SHA256_HEX.fullmatch(expected)
        ):
            raise ValueError(
                f"run_manifest.json has an invalid artifact hash: {name!r}: {expected!r}"
            )
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"run_manifest.json has an invalid artifact path: {name!r}")
        source = artifacts_dir / relative
        if not source.is_file():
            raise FileNotFoundError(f"run_manifest.json lists a missing artifact: {source}")
        actual = sha256_file(source)
        if actual != expected.lower():
            raise ValueError(
                f"manifest hash mismatch for {source}: expected {expected.lower()}, got {actual}"
            )
    return manifest


def _dashboard_files(dashboard_dir: Path) -> tuple[list[Path], list[Path]]:
    power_bi = sorted(
        source for pattern in DASHBOARD_GLOBS for source in dashboard_dir.glob(pattern)
    )
    screenshots = sorted(dashboard_dir.glob(SCREENSHOT_GLOB))
    if not power_bi:
        raise FileNotFoundError(
            f"dashboard has no Power BI file (*.pbix or *.pbip): {dashboard_dir}"
        )
    if not screenshots:
        raise FileNotFoundError(f"dashboard has no screenshot (screenshots/*.png): {dashboard_dir}")
    return power_bi, screenshots


def _validate_inputs(
    artifacts_dir: Path,
    dashboard_dir: Path,
    repo_root: Path,
) -> tuple[dict, dict, list[Path], list[Path]]:
    for name in ROOT_FILES:
        source = repo_root / name
        if not source.is_file():
            raise FileNotFoundError(f"missing required root file: {source}")

    for name in DOC_FILES:
        source = repo_root / name
        if not source.is_file():
            raise FileNotFoundError(f"missing required doc: {source}")

    for name in ARTIFACT_FILES:
        source = artifacts_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"missing release artifact: {source}")

    power_bi, screenshots = _dashboard_files(dashboard_dir)

    quality = _read_json(artifacts_dir / "quality_report.json")
    if quality["gate"]["blocked"]:
        raise RuntimeError("quality gate is blocked; refusing to build a release")

    _verify_artifact_checksums(artifacts_dir)
    manifest = _verify_run_manifest(artifacts_dir)
    return manifest, quality, power_bi, screenshots


def _release_notes(version: str, manifest: dict, quality: dict) -> str:
    counts = manifest["counts"]
    summary = quality["summary"]
    return f"""# ContrataMYPE {version}

Cohorte 2025 construida desde el bulk OCDS del OECE.

## Cifras

- Actualizaciones procesadas: {counts["tenders"]:,}
- Procesos en la cohorte 2025: {counts["cohort_records"]:,}
- Oportunidades compatibles MYPE: {counts["mype_opportunities"]:,}
- Compradores: {counts["buyers"]:,}
- Proveedores: {counts["suppliers"]:,}
- Awards (filas por proveedor): {counts["awards"]:,}
- Contratos: {counts["contracts"]:,}

## Calidad

- Checks: {summary["total_checks"]} ({summary["passed_checks"]} pass,
  {summary["warn_checks"]} warn, {summary["failed_checks"]} fail)
- Gate: {"bloqueado" if quality["gate"]["blocked"] else "abierto"}

## Contenido

- `artifacts/`: Parquet/CSV, reporte de calidad, manifest y checksums del pipeline.
- `dashboard/`: PBIP/PBIX y capturas.
- `docs/`: diccionario, arquitectura, perfil de datos y límites.
- `SHA256SUMS`: hash de cada archivo del bundle.

## Atribución

Datos: OECE, Portal de Contrataciones Abiertas, estándar OCDS, CC BY 4.0.
La regla MYPE es una heurística de compatibilidad, no elegibilidad legal.
"""


def _replace_bundle(tmp_dir: Path, out_dir: Path) -> None:
    """Swap the freshly built bundle in, keeping the old one until the swap works."""
    backup_dir = out_dir.with_name(out_dir.name + ".old")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    if out_dir.exists():
        out_dir.rename(backup_dir)
    try:
        tmp_dir.rename(out_dir)
    except OSError:
        if backup_dir.exists():
            backup_dir.rename(out_dir)
        raise
    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)


def build_release(
    version: str,
    artifacts_dir: Path,
    dashboard_dir: Path,
    out_dir: Path,
    repo_root: Path = REPO_ROOT,
) -> dict:
    artifacts_dir = Path(artifacts_dir)
    dashboard_dir = Path(dashboard_dir)
    out_dir = Path(out_dir)

    manifest, quality, power_bi, screenshots = _validate_inputs(
        artifacts_dir, dashboard_dir, repo_root
    )

    tmp_dir = out_dir.with_name(out_dir.name + ".tmp")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    try:
        copied: list[str] = []
        for name in ARTIFACT_FILES:
            _copy(artifacts_dir / name, tmp_dir / "artifacts" / name)
            copied.append(f"artifacts/{name}")

        for name in ROOT_FILES:
            _copy(repo_root / name, tmp_dir / name)
            copied.append(name)

        for name in DOC_FILES:
            _copy(repo_root / name, tmp_dir / "docs" / Path(name).name)
            copied.append(f"docs/{Path(name).name}")

        for source in power_bi:
            _copy(source, tmp_dir / "dashboard" / source.name)
            copied.append(f"dashboard/{source.name}")
        for source in screenshots:
            _copy(source, tmp_dir / "dashboard" / "screenshots" / source.name)
            copied.append(f"dashboard/screenshots/{source.name}")

        notes = _release_notes(version, manifest, quality)
        (tmp_dir / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")
        copied.append("RELEASE_NOTES.md")

        checksums = []
        for relative in sorted(copied):
            digest = sha256_file(tmp_dir / relative)
            checksums.append(f"{digest}  {relative}")
        (tmp_dir / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
        span_bytes = sum((tmp_dir / name).stat().st_size for name in copied)
    except BaseException:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    _replace_bundle(tmp_dir, out_dir)

    return {
        "version": version,
        "out_dir": str(out_dir),
        "files": len(copied) + 1,
        "span_bytes": span_bytes,
        "gate": quality["gate"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_release")
    parser.add_argument("--version", default="v1.0.0")
    parser.add_argument("--artifacts", type=Path, default=REPO_ROOT / "artifacts" / "2025")
    parser.add_argument("--dashboard", type=Path, default=REPO_ROOT / "dashboard")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    out_dir = args.out or REPO_ROOT / "dist" / args.version
    summary = build_release(args.version, args.artifacts, args.dashboard, out_dir)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
