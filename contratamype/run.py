"""Pipeline orchestration: ingest -> DuckDB -> quality gate -> artifacts."""

from __future__ import annotations

import time
from pathlib import Path

from contratamype import exports, ingest, store
from contratamype.config import Settings
from contratamype.quality import run_checks


def run_pipeline(input_path: Path, settings: Settings) -> dict:
    input_path = Path(input_path)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    input_sha256 = exports.sha256_file(input_path)
    timings: dict[str, float] = {}
    total_started = time.perf_counter()

    started = time.perf_counter()
    conn = store.connect(settings.db_path)
    try:
        store.init_schema(conn)
        stats = ingest.RawStats()
        store.load(
            conn,
            ingest.iter_normalized(input_path, settings, stats),
            batch_size=settings.batch_size,
        )
        timings["ingest_ms"] = round((time.perf_counter() - started) * 1000, 2)

        started = time.perf_counter()
        quality = run_checks(conn, settings, stats)
        timings["quality_ms"] = round((time.perf_counter() - started) * 1000, 2)
        exports.write_quality_report(quality, settings.artifacts_dir)

        counts = store.counts(conn, settings.cohort_year)
        summary = {
            "status": "blocked" if quality["gate"]["blocked"] else "ok",
            "input": str(input_path),
            "input_sha256": input_sha256,
            **counts,
            "quality_summary": quality["summary"],
            "quality_gate": quality["gate"],
            "timings_ms": timings,
            "artifacts_dir": str(settings.artifacts_dir),
            "db_path": str(settings.db_path),
        }

        started = time.perf_counter()
        if not quality["gate"]["blocked"]:
            exports.export_parquet(conn, settings.artifacts_dir)
            exports.export_mype_csv(conn, settings.artifacts_dir, settings)
        timings["export_ms"] = round((time.perf_counter() - started) * 1000, 2)
        timings["total_ms"] = round((time.perf_counter() - total_started) * 1000, 2)

        exports.write_checksums(settings.artifacts_dir)
        manifest_path = exports.write_manifest(
            settings.artifacts_dir,
            summary,
            quality,
            input_sha256,
            timings,
            settings,
        )
        summary["run_manifest"] = str(manifest_path)
        return summary
    finally:
        conn.close()
