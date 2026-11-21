"""Artifacts: quality report, Parquet/CSV exports, manifest and checksums."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from contratamype.config import Settings

PAYLOAD_NAMES = (
    "quality_report.json",
    "tenders.parquet",
    "awards.parquet",
    "contracts.parquet",
    "buyers.parquet",
    "suppliers.parquet",
    "mype_opportunities.csv",
)

TABLES = ("tenders", "awards", "contracts", "buyers", "suppliers")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def write_quality_report(report: dict, artifacts_dir: Path) -> Path:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    path = artifacts_dir / "quality_report.json"
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def export_parquet(conn: duckdb.DuckDBPyConnection, artifacts_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for table in TABLES:
        path = artifacts_dir / f"{table}.parquet"
        conn.execute(f"COPY (SELECT * FROM {table}) TO '{_sql_path(path)}' (FORMAT PARQUET)")
        paths.append(path)
    return paths


def export_mype_csv(
    conn: duckdb.DuckDBPyConnection,
    artifacts_dir: Path,
    settings: Settings,
) -> Path:
    path = artifacts_dir / "mype_opportunities.csv"
    query = f"""
        SELECT ocid, title, description, category, amount_pen, currency,
               department, buyer_name, tender_start, tender_end,
               segmentation_id, mype_fit
        FROM tenders
        WHERE segmentation_year = {int(settings.cohort_year)}
          AND mype_fit = true
        ORDER BY amount_pen DESC, ocid
    """
    conn.execute(f"COPY ({query}) TO '{_sql_path(path)}' (FORMAT CSV, HEADER, DELIMITER ',')")
    return path


def write_checksums(artifacts_dir: Path) -> Path:
    existing = [artifacts_dir / name for name in PAYLOAD_NAMES if (artifacts_dir / name).exists()]
    lines = [f"{sha256_file(path)}  {path.name}" for path in sorted(existing, key=lambda p: p.name)]
    target = artifacts_dir / "checksums.sha256"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def write_manifest(
    artifacts_dir: Path,
    summary: dict,
    quality: dict,
    input_sha256: str,
    timings: dict,
) -> Path:
    artifact_hashes = {
        name: sha256_file(artifacts_dir / name)
        for name in PAYLOAD_NAMES
        if (artifacts_dir / name).exists()
    }
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "input": summary["input"],
        "input_sha256": input_sha256,
        "counts": {
            key: summary[key]
            for key in (
                "raw_records",
                "tenders",
                "buyers",
                "suppliers",
                "awards",
                "contracts",
                "cohort_records",
                "mype_opportunities",
            )
        },
        "quality_summary": quality["summary"],
        "quality_gate": quality["gate"],
        "timings_ms": timings,
        "artifacts_sha256": artifact_hashes,
        "checksums_note": (
            "checksums.sha256 covers the payload artifacts; it cannot cover "
            "run_manifest.json or itself without a circular dependency."
        ),
    }
    path = artifacts_dir / "run_manifest.json"
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return path
