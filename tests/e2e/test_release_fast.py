"""Fast E2E for the local release bundle: contents, checksums and gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_release import ARTIFACT_FILES, build_release


def fake_inputs(tmp_path: Path, *, blocked: bool = False) -> tuple[Path, Path, Path]:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    manifest = {
        "counts": {
            "tenders": 3,
            "cohort_records": 2,
            "mype_opportunities": 1,
            "buyers": 2,
            "suppliers": 2,
            "awards": 2,
            "contracts": 2,
        }
    }
    quality = {
        "summary": {
            "total_checks": 12,
            "passed_checks": 9,
            "warn_checks": 3,
            "failed_checks": 0,
        },
        "gate": {"blocked": blocked, "blocking_checks": []},
    }
    (artifacts / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifacts / "quality_report.json").write_text(json.dumps(quality), encoding="utf-8")
    for name in ARTIFACT_FILES:
        if name not in {"run_manifest.json", "quality_report.json"}:
            (artifacts / name).write_bytes(f"content of {name}".encode())

    dashboard = tmp_path / "dashboard"
    (dashboard / "screenshots").mkdir(parents=True)
    (dashboard / "dashboard.pbix").write_bytes(b"fake-pbix")
    (dashboard / "screenshots" / "page-1.png").write_bytes(b"fake-png")

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# demo", encoding="utf-8")
    return artifacts, dashboard, repo


@pytest.mark.fast
def test_release_bundle_is_complete_and_verifiable(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    out = tmp_path / "dist" / "v1.0.0"
    summary = build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)

    assert summary["gate"]["blocked"] is False
    assert (out / "artifacts" / "tenders.parquet").exists()
    assert (out / "artifacts" / "quality_report.json").exists()
    assert (out / "dashboard" / "dashboard.pbix").exists()
    assert (out / "dashboard" / "screenshots" / "page-1.png").exists()
    assert (out / "docs" / "README.md").exists()
    assert not (out / "data").exists()

    lines = (out / "SHA256SUMS").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == summary["files"] - 1
    for line in lines:
        digest, relative = line.split("  ", 1)
        assert hashlib.sha256((out / relative).read_bytes()).hexdigest() == digest

    first = (out / "SHA256SUMS").read_text(encoding="utf-8")
    build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)
    assert (out / "SHA256SUMS").read_text(encoding="utf-8") == first


@pytest.mark.fast
def test_release_bundle_refuses_blocked_gate(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path, blocked=True)
    with pytest.raises(RuntimeError, match="quality gate is blocked"):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_fails_on_missing_artifact(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    (artifacts / "tenders.parquet").unlink()
    with pytest.raises(FileNotFoundError, match="tenders.parquet"):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)
