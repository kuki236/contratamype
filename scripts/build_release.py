"""Build a local release bundle with checksums.

The bundle never includes raw data. It is deterministic: the same inputs produce
the same SHA256SUMS (no timestamps in the manifest).
"""

from __future__ import annotations

import argparse
import hashlib
import json
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
    "docs/quality-checks.md",
    "docs/market-findings-2025.md",
    "docs/llm-policy.md",
    "docs/llm-eval-sample-2025.json",
    "docs/release.md",
    "docs/user-test-v1.0.0.md",
    "docs/web.md",
    "docs/powerbi.md",
    "docs/alerts.md",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


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
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    manifest_path = artifacts_dir / "run_manifest.json"
    quality_path = artifacts_dir / "quality_report.json"
    if not manifest_path.exists() or not quality_path.exists():
        raise FileNotFoundError("run_manifest.json and quality_report.json are required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    if quality["gate"]["blocked"]:
        raise RuntimeError("quality gate is blocked; refusing to build a release")

    copied: list[str] = []
    for name in ARTIFACT_FILES:
        source = artifacts_dir / name
        if not source.exists():
            raise FileNotFoundError(f"missing release artifact: {source}")
        _copy(source, out_dir / "artifacts" / name)
        copied.append(f"artifacts/{name}")

    for name in ROOT_FILES:
        source = repo_root / name
        if source.exists():
            _copy(source, out_dir / name)
            copied.append(name)

    for name in DOC_FILES:
        source = repo_root / name
        if source.exists():
            _copy(source, out_dir / "docs" / Path(name).name)
            copied.append(f"docs/{Path(name).name}")

    dashboard_files = sorted(dashboard_dir.glob("*.pbix")) + sorted(dashboard_dir.glob("*.pbip"))
    for source in dashboard_files:
        _copy(source, out_dir / "dashboard" / source.name)
        copied.append(f"dashboard/{source.name}")
    for source in sorted(dashboard_dir.glob("screenshots/*.png")):
        _copy(source, out_dir / "dashboard" / "screenshots" / source.name)
        copied.append(f"dashboard/screenshots/{source.name}")

    notes = _release_notes(version, manifest, quality)
    (out_dir / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")
    copied.append("RELEASE_NOTES.md")

    checksums = []
    for relative in sorted(copied):
        digest = sha256_file(out_dir / relative)
        checksums.append(f"{digest}  {relative}")
    (out_dir / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")

    return {
        "version": version,
        "out_dir": str(out_dir),
        "files": len(copied) + 1,
        "span_bytes": sum((out_dir / name).stat().st_size for name in copied),
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
