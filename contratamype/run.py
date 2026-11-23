"""Pipeline orchestration: ingest -> DuckDB -> quality gate -> artifacts."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from contratamype import exports, ingest, store
from contratamype.config import Settings
from contratamype.quality import run_checks


@dataclass(slots=True)
class InputFile:
    path: Path
    sha256: str
    bytes: int
    snapshot_year: int
    records: int = 0

    def manifest(self) -> dict:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "bytes": self.bytes,
            "records": self.records,
        }


def _input_files(input_paths: Path | list[Path], settings: Settings) -> list[InputFile]:
    paths = [Path(input_paths)] if isinstance(input_paths, (str, Path)) else list(input_paths)
    if not paths:
        raise ValueError("at least one input is required")
    files = [
        InputFile(
            path=path,
            sha256=exports.sha256_file(path),
            bytes=path.stat().st_size,
            snapshot_year=ingest.snapshot_year_for(path, settings.cohort_year),
        )
        for path in paths
    ]
    return sorted(files, key=lambda item: (item.snapshot_year, item.path.name))


def run_pipeline(input_paths: Path | list[Path], settings: Settings) -> dict:
    files = _input_files(input_paths, settings)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    input_sha256 = exports.combined_input_sha256([item.manifest() for item in files])
    timings: dict[str, float] = {}
    total_started = time.perf_counter()

    started = time.perf_counter()
    conn = store.connect(settings.db_path)
    try:
        store.init_schema(conn)
        stats = ingest.RawStats()

        def records():
            for item in files:
                before = stats.records
                yield from ingest.iter_normalized(
                    item.path,
                    settings,
                    stats,
                    item.snapshot_year,
                )
                item.records = stats.records - before

        store.load(conn, records(), batch_size=settings.batch_size)
        timings["ingest_ms"] = round((time.perf_counter() - started) * 1000, 2)

        started = time.perf_counter()
        quality = run_checks(conn, settings, stats)
        timings["quality_ms"] = round((time.perf_counter() - started) * 1000, 2)
        exports.write_quality_report(quality, settings.artifacts_dir)

        counts = store.counts(conn, settings.cohort_years)
        inputs = [item.manifest() for item in files]
        assert exports.combined_input_sha256(inputs) == input_sha256
        summary = {
            "status": "blocked" if quality["gate"]["blocked"] else "ok",
            "input": str(files[0].path) if len(files) == 1 else [str(item.path) for item in files],
            "inputs": inputs,
            "input_sha256": input_sha256,
            **counts,
            "cohort_years": list(settings.cohort_years),
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
