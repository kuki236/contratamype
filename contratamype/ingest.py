"""Stream OCDS JSONL and yield normalized records."""

from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from contratamype.config import Settings
from contratamype.normalize import Normalized, normalize_release


@dataclass(slots=True)
class RawStats:
    lines: int = 0
    parse_errors: int = 0
    missing_ocid: int = 0
    missing_tender: int = 0
    records: int = 0


def iter_releases(payload: dict) -> Iterator[dict]:
    compiled = payload.get("compiledRelease")
    if isinstance(compiled, dict):
        yield compiled
        return
    records = payload.get("records")
    if isinstance(records, list):
        for record in records:
            if isinstance(record.get("compiledRelease"), dict):
                yield record["compiledRelease"]
            elif isinstance(record, dict):
                yield record
        return
    release = payload.get("release")
    if isinstance(release, dict):
        yield release
        return
    yield payload


def iter_normalized(
    path: Path,
    settings: Settings,
    stats: RawStats,
) -> Iterator[Normalized]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            stats.lines += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                stats.parse_errors += 1
                continue
            for release in iter_releases(payload):
                ocid = release.get("ocid")
                if not ocid:
                    stats.missing_ocid += 1
                    continue
                if not release.get("tender"):
                    stats.missing_tender += 1
                stats.records += 1
                yield normalize_release(release, settings)
