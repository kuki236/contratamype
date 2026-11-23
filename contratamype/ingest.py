"""Stream OCDS JSONL and yield normalized records."""

from __future__ import annotations

import gzip
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from contratamype.config import Settings
from contratamype.normalize import Normalized, normalize_release


@dataclass(slots=True)
class RawStats:
    lines: int = 0
    parse_errors: int = 0
    missing_ocid: int = 0
    missing_tender: int = 0
    missing_title: int = 0
    records: int = 0
    parse_error_lines: list[int] = field(default_factory=list)
    schema_samples: list[dict[str, Any]] = field(default_factory=list)

    def sample(self, payload: dict[str, Any]) -> None:
        if len(self.schema_samples) < 5:
            self.schema_samples.append(payload)


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


YEAR_PATTERN = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")


def snapshot_year_for(path: Path, default: int) -> int:
    match = YEAR_PATTERN.search(path.name)
    return int(match.group(1)) if match else int(default)


def iter_normalized(
    path: Path,
    settings: Settings,
    stats: RawStats,
    snapshot_year: int,
) -> Iterator[Normalized]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            stats.lines += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                stats.parse_errors += 1
                if len(stats.parse_error_lines) < 5:
                    stats.parse_error_lines.append(line_number)
                continue
            for release in iter_releases(payload):
                ocid = release.get("ocid")
                if not ocid:
                    stats.missing_ocid += 1
                    stats.sample({"line": line_number, "missing": "ocid"})
                    continue
                tender = release.get("tender")
                if not isinstance(tender, dict) or not tender:
                    stats.missing_tender += 1
                    stats.sample({"line": line_number, "ocid": ocid, "missing": "tender"})
                    continue
                title = tender.get("title")
                if title is None or not str(title).strip():
                    stats.missing_title += 1
                    stats.sample({"line": line_number, "ocid": ocid, "missing": "title"})
                stats.records += 1
                yield normalize_release(release, settings, snapshot_year)
