"""Fast E2E for the local release bundle: validation, atomic build and verification."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

import scripts.build_release as build_release_module
from scripts.build_release import ARTIFACT_FILES, DOC_FILES, ROOT_FILES, build_release

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_release.py"

PAYLOAD_FILES = tuple(
    name for name in ARTIFACT_FILES if name not in {"run_manifest.json", "checksums.sha256"}
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fake_inputs(tmp_path: Path, *, blocked: bool = False) -> tuple[Path, Path, Path]:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    for name in PAYLOAD_FILES:
        if name != "quality_report.json":
            (artifacts / name).write_bytes(f"content of {name}".encode())

    quality = {
        "summary": {
            "total_checks": 12,
            "passed_checks": 9,
            "warn_checks": 3,
            "failed_checks": 0,
        },
        "gate": {"blocked": blocked, "blocking_checks": []},
    }
    (artifacts / "quality_report.json").write_text(json.dumps(quality), encoding="utf-8")

    manifest = {
        "input_sha256": hashlib.sha256(b"fake-bulk").hexdigest(),
        "counts": {
            "tenders": 3,
            "cohort_records": 2,
            "mype_opportunities": 1,
            "buyers": 2,
            "suppliers": 2,
            "awards": 2,
            "contracts": 2,
        },
        "artifacts_sha256": {name: _sha256(artifacts / name) for name in sorted(PAYLOAD_FILES)},
    }
    (artifacts / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    checksums = [f"{_sha256(artifacts / name)}  {name}" for name in sorted(PAYLOAD_FILES)]
    (artifacts / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")

    dashboard = tmp_path / "dashboard"
    (dashboard / "screenshots").mkdir(parents=True)
    (dashboard / "dashboard.pbix").write_bytes(b"fake-pbix")
    (dashboard / "screenshots" / "page-1.png").write_bytes(b"fake-png")

    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    for name in ROOT_FILES:
        (repo / name).write_text(f"# {name}", encoding="utf-8")
    for name in DOC_FILES:
        (repo / name).write_text(f"# {name}", encoding="utf-8")
    (repo / ".env").write_text("SECRET=1", encoding="utf-8")
    (repo / "data" / "raw").mkdir(parents=True)
    (repo / "data" / "raw" / "bulk.jsonl.gz").write_bytes(b"raw")
    return artifacts, dashboard, repo


def _run_verify(root: Path) -> tuple[int, dict]:
    completed = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    return completed.returncode, json.loads(completed.stdout)


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
    assert (out / "README.md").exists()
    assert (out / "README.en.md").exists()
    assert (out / "LICENSE").exists()
    for name in DOC_FILES:
        assert (out / "docs" / Path(name).name).exists()
    assert "v1.0.0" in (out / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert not (out / "data").exists()
    assert not (out / ".env").exists()

    lines = (out / "SHA256SUMS").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == summary["files"] - 1
    for line in lines:
        digest, relative = line.split("  ", 1)
        assert hashlib.sha256((out / relative).read_bytes()).hexdigest() == digest


@pytest.mark.fast
def test_release_bundle_uses_notes_file(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    out = tmp_path / "dist" / "v1.1.1"
    notes = tmp_path / "notes.md"
    notes.write_text("# ContrataMYPE v1.1.1\n\nPatch notes.\n", encoding="utf-8")
    build_release("v1.1.1", artifacts, dashboard, out, repo_root=repo, notes_file=notes)
    assert (out / "RELEASE_NOTES.md").read_text(encoding="utf-8") == notes.read_text(
        encoding="utf-8"
    )


@pytest.mark.fast
def test_release_bundle_rejects_empty_notes_file(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    notes = tmp_path / "notes.md"
    notes.write_text("  \n", encoding="utf-8")
    with pytest.raises(ValueError, match="release notes file is empty"):
        build_release(
            "v1.1.1",
            artifacts,
            dashboard,
            tmp_path / "dist",
            repo_root=repo,
            notes_file=notes,
        )


@pytest.mark.fast
def test_release_bundle_refuses_blocked_gate(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path, blocked=True)
    out = tmp_path / "dist" / "v1.0.0"
    with pytest.raises(RuntimeError, match="quality gate is blocked"):
        build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)
    assert not out.exists()
    assert not out.with_name(out.name + ".tmp").exists()


@pytest.mark.fast
def test_release_bundle_fails_on_missing_artifact(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    (artifacts / "tenders.parquet").unlink()
    with pytest.raises(FileNotFoundError, match="tenders.parquet"):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_requires_power_bi_file(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    (dashboard / "dashboard.pbix").unlink()
    expected = f"dashboard has no Power BI file (*.pbix or *.pbip): {dashboard}"
    with pytest.raises(FileNotFoundError, match=re.escape(expected)):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_requires_dashboard_screenshot(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    (dashboard / "screenshots" / "page-1.png").unlink()
    expected = f"dashboard has no screenshot (screenshots/*.png): {dashboard}"
    with pytest.raises(FileNotFoundError, match=re.escape(expected)):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_requires_every_doc(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    missing = repo / "docs" / "powerbi.md"
    missing.unlink()
    with pytest.raises(FileNotFoundError, match=re.escape(f"missing required doc: {missing}")):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_requires_every_root_file(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    missing = repo / "LICENSE"
    missing.unlink()
    expected = f"missing required root file: {missing}"
    with pytest.raises(FileNotFoundError, match=re.escape(expected)):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_rejects_corrupted_artifact_checksum(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    (artifacts / "tenders.parquet").write_bytes(b"tampered")
    expected = f"checksum mismatch in checksums.sha256 for {artifacts / 'tenders.parquet'}"
    with pytest.raises(ValueError, match=re.escape(expected)):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_rejects_corrupted_manifest_hash(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    manifest_path = artifacts / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts_sha256"]["tenders.parquet"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    expected = f"manifest hash mismatch for {artifacts / 'tenders.parquet'}"
    with pytest.raises(ValueError, match=re.escape(expected)):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_release_bundle_requires_valid_input_sha256(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    manifest_path = artifacts / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["input_sha256"] = "not-a-hash"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    expected = "run_manifest.json input_sha256 must be 64 hex characters"
    with pytest.raises(ValueError, match=re.escape(expected)):
        build_release("v1.0.0", artifacts, dashboard, tmp_path / "dist", repo_root=repo)


@pytest.mark.fast
def test_failed_rebuild_preserves_previous_bundle(tmp_path: Path, monkeypatch) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    out = tmp_path / "dist" / "v1.0.0"
    build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)

    sums_before = (out / "SHA256SUMS").read_text(encoding="utf-8")
    parquet_before = (out / "artifacts" / "tenders.parquet").read_bytes()
    tmp_dir = out.with_name(out.name + ".tmp")

    original_copy = build_release_module._copy
    calls = {"count": 0}

    def failing_copy(source: Path, target: Path) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("disk full")
        original_copy(source, target)

    monkeypatch.setattr(build_release_module, "_copy", failing_copy)
    with pytest.raises(OSError, match="disk full"):
        build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)

    assert out.is_dir()
    assert not tmp_dir.exists()
    assert (out / "SHA256SUMS").read_text(encoding="utf-8") == sums_before
    assert (out / "artifacts" / "tenders.parquet").read_bytes() == parquet_before

    monkeypatch.undo()
    (artifacts / "tenders.parquet").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)

    assert out.is_dir()
    assert not tmp_dir.exists()
    assert (out / "SHA256SUMS").read_text(encoding="utf-8") == sums_before
    assert (out / "artifacts" / "tenders.parquet").read_bytes() == parquet_before


@pytest.mark.fast
def test_release_bundle_sha256sums_are_deterministic(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    out = tmp_path / "dist" / "v1.0.0"
    build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)
    first = (out / "SHA256SUMS").read_text(encoding="utf-8")

    build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)
    assert (out / "SHA256SUMS").read_text(encoding="utf-8") == first


@pytest.mark.fast
def test_verify_release_accepts_good_bundle(tmp_path: Path) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    out = tmp_path / "dist" / "v1.0.0"
    summary = build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)

    returncode, payload = _run_verify(out)
    assert returncode == 0
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert payload["files"] == summary["files"]
    assert payload["checksums_verified"] == summary["files"] - 1


def _tamper_readme(root: Path) -> None:
    (root / "README.md").write_text("tampered", encoding="utf-8")


def _add_env(root: Path) -> None:
    (root / ".env").write_text("SECRET=1", encoding="utf-8")


def _add_raw_data(root: Path) -> None:
    path = root / "data" / "raw" / "bulk.jsonl.gz"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"raw")


def _remove_doc(root: Path) -> None:
    (root / "docs" / "architecture.md").unlink()


def _remove_power_bi(root: Path) -> None:
    (root / "dashboard" / "dashboard.pbix").unlink()


def _remove_screenshot(root: Path) -> None:
    (root / "dashboard" / "screenshots" / "page-1.png").unlink()


def _remove_sums(root: Path) -> None:
    (root / "SHA256SUMS").unlink()


@pytest.mark.fast
@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (_tamper_readme, "SHA256SUMS mismatch for"),
        (_add_env, "environment file is not allowed"),
        (_add_raw_data, "raw data is not allowed"),
        (_remove_doc, "missing required file"),
        (_remove_power_bi, "missing dashboard Power BI file"),
        (_remove_screenshot, "missing dashboard screenshot"),
        (_remove_sums, "missing SHA256SUMS"),
    ],
)
def test_verify_release_rejects_bad_bundle(
    tmp_path: Path, mutate: Callable[[Path], None], message: str
) -> None:
    artifacts, dashboard, repo = fake_inputs(tmp_path)
    out = tmp_path / "dist" / "v1.0.0"
    build_release("v1.0.0", artifacts, dashboard, out, repo_root=repo)
    mutate(out)

    returncode, payload = _run_verify(out)
    assert returncode == 1
    assert payload["ok"] is False
    assert any(message in error for error in payload["errors"]), payload["errors"]
