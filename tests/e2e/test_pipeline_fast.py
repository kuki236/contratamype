"""Fast E2E: medium-hard OCDS fixture through the real CLI/artifacts.

The fixture is intentionally dirty: duplicate OCID, amount 0, negative amount,
invalid category, missing department, missing buyer, award without supplier,
award without contract, supplier without address and contract without award.
The test proves the quality gate and the artifacts, not just that the code runs.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BULK = REPO_ROOT / "data" / "raw" / "ocds" / "2025.jsonl.gz"


def _release(
    ocid: str,
    *,
    title: str | None = None,
    category: str = "goods",
    amount: float = 100_000,
    start: str = "2025-02-01",
    end: str = "2025-02-10",
    department: str | None = "LIMA",
    buyer: bool = True,
    buyer_party: bool = True,
    award: bool = True,
    award_supplier: bool = True,
    supplier_address: bool = True,
    contract: bool = True,
    contract_award: bool = True,
) -> dict:
    buyer_id = f"PE-CONSUCODE-{ocid}"
    supplier_id = f"PE-RUC-{ocid}"
    parties = []
    if buyer_party:
        address = {"department": department} if department else {"countryName": "PERU"}
        parties.append(
            {
                "id": buyer_id,
                "name": f"BUYER {ocid}",
                "roles": ["buyer", "procuringEntity"],
                "address": address,
                "additionalIdentifiers": [{"scheme": "PE-RUC", "id": "20100000001"}],
            }
        )
    if award:
        supplier = {
            "id": supplier_id,
            "name": f"SUPPLIER {ocid}",
            "roles": ["supplier", "tenderer"],
        }
        if supplier_address:
            supplier["address"] = {"department": department or "LIMA"}
        parties.append(supplier)
    release = {
        "ocid": ocid,
        "date": "2025-02-01T10:00:00-05:00",
        "dataSegmentation": {"id": "2025-02", "criteria": ["añoInicioConvocatoria"]},
        "tender": {
            "title": title if title is not None else f"TENDER {ocid}",
            "description": f"DESCRIPTION {ocid}",
            "mainProcurementCategory": category,
            "procurementMethodDetails": "Adjudicación Simplificada",
            "value": {"amount": amount, "currency": "PEN", "amount_PEN": amount},
            "tenderPeriod": {"startDate": start, "endDate": end},
            "status": "active",
        },
        "parties": parties,
    }
    if buyer:
        release["buyer"] = {"id": buyer_id, "name": f"BUYER {ocid}"}
    if award:
        suppliers = [{"id": supplier_id, "name": f"SUPPLIER {ocid}"}] if award_supplier else []
        release["awards"] = [
            {
                "id": f"award-{ocid}",
                "suppliers": suppliers,
                "value": {"amount": amount, "currency": "PEN", "amount_PEN": amount},
                "date": "2025-02-15",
                "status": "awarded",
            }
        ]
    if contract:
        contract_row = {
            "id": f"contract-{ocid}",
            "value": {"amount": amount, "currency": "PEN", "amount_PEN": amount},
            "dateSigned": "2025-02-20",
            "status": "active",
        }
        if contract_award:
            contract_row["awardID"] = f"award-{ocid}"
        release["contracts"] = [contract_row]
    return {"ocid": ocid, "compiledRelease": release}


def hard_records() -> list[dict]:
    return [
        _release("ocds-hard-001"),
        _release("ocds-hard-001", title="DUPLICADO"),
        _release(
            "ocds-hard-002",
            category="services",
            amount=0,
            start="2025-03-01",
            end="2025-03-01",
            department="CUSCO",
            award=False,
            contract=False,
        ),
        _release(
            "ocds-hard-003",
            category="other",
            amount=-10,
            department="LIMA",
            award=False,
            contract=False,
        ),
        _release(
            "ocds-hard-004",
            category="works",
            amount=50_000,
            department=None,
            award=False,
            contract=False,
        ),
        _release(
            "ocds-hard-005",
            category="goods",
            amount=20_000,
            department="PIURA",
            award_supplier=False,
            contract_award=False,
        ),
        _release(
            "ocds-hard-006",
            category="services",
            amount=30_000,
            department="LIMA",
            buyer=False,
            buyer_party=True,
            award=False,
            contract=False,
        ),
        _release(
            "ocds-hard-007",
            category="goods",
            amount=150_000,
            supplier_address=False,
            contract=False,
        ),
    ]


def clean_records() -> list[dict]:
    return [
        _release("ocds-clean-001"),
        _release(
            "ocds-clean-002",
            category="services",
            amount=50_000,
            department="CUSCO",
            start="2025-03-01",
            end="2025-03-05",
        ),
    ]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


def settings(tmp_path: Path):
    from contratamype.config import Settings

    return Settings(
        artifacts_dir=tmp_path / "artifacts",
        db_path=tmp_path / "contratamype.duckdb",
    )


def verify_checksums(artifacts: Path) -> None:
    lines = (artifacts / "checksums.sha256").read_text(encoding="utf-8").strip().splitlines()
    assert lines
    for line in lines:
        digest, name = line.split("  ", 1)
        actual = hashlib.sha256((artifacts / name).read_bytes()).hexdigest()
        assert actual == digest, name


@pytest.mark.fast
def test_hard_fixture_blocks_and_reports_exact_counts(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    input_path = tmp_path / "hard.jsonl"
    write_jsonl(input_path, hard_records())
    artifacts = tmp_path / "artifacts"
    summary = run_pipeline(input_path, settings(tmp_path))

    assert summary["tenders"] == 7
    assert summary["awards"] == 3
    assert summary["contracts"] == 2
    assert summary["buyers"] == 6
    assert summary["suppliers"] == 2

    connection = duckdb.connect(str(tmp_path / "contratamype.duckdb"), read_only=True)
    try:
        missing_address = connection.execute(
            "SELECT COUNT(*) FROM suppliers WHERE department IS NULL"
        ).fetchone()[0]
    finally:
        connection.close()
    assert missing_address == 1
    assert summary["cohort_records"] == 7
    assert summary["quality_gate"]["blocked"] is True
    assert summary["quality_summary"] == {
        "total_checks": 12,
        "failed_checks": 5,
        "warn_checks": 4,
        "passed_checks": 3,
    }

    report = json.loads((artifacts / "quality_report.json").read_text(encoding="utf-8"))
    failed = {
        check["name"]: check["rows_failed"]
        for check in report["checks"]
        if check["status"] == "fail"
    }
    warned = {
        check["name"]: check["rows_failed"]
        for check in report["checks"]
        if check["status"] == "warn"
    }
    assert failed == {
        "ocid_unique": 1,
        "category_valid": 1,
        "department_valid": 1,
        "buyer_present": 1,
        "amount_non_negative": 1,
    }
    assert warned == {
        "amount_zero": 1,
        "period_start_eq_end": 1,
        "award_supplier_present": 1,
        "contract_award_linked": 1,
    }
    assert not (artifacts / "tenders.parquet").exists()
    assert (artifacts / "run_manifest.json").exists()
    verify_checksums(artifacts)

    manifest = json.loads((artifacts / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_sha256"] == hashlib.sha256(input_path.read_bytes()).hexdigest()


@pytest.mark.fast
def test_clean_fixture_passes_and_exports(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    input_path = tmp_path / "clean.jsonl"
    write_jsonl(input_path, clean_records())
    artifacts = tmp_path / "artifacts"
    summary = run_pipeline(input_path, settings(tmp_path))

    assert summary["tenders"] == 2
    assert summary["cohort_records"] == 2
    assert summary["mype_opportunities"] == 2
    assert summary["quality_gate"]["blocked"] is False
    assert summary["quality_summary"]["failed_checks"] == 0
    assert summary["quality_summary"]["warn_checks"] == 0
    assert (artifacts / "tenders.parquet").exists()
    assert (artifacts / "mype_opportunities.csv").exists()
    assert len((artifacts / "mype_opportunities.csv").read_text(encoding="utf-8").splitlines()) == 3
    verify_checksums(artifacts)


@pytest.mark.fast
def test_cli_returns_nonzero_when_gate_blocks(tmp_path: Path) -> None:
    input_path = tmp_path / "hard.jsonl"
    write_jsonl(input_path, hard_records())
    artifacts = tmp_path / "artifacts"
    db_path = tmp_path / "cli.duckdb"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "contratamype",
            "run",
            "--input",
            str(input_path),
            "--artifacts",
            str(artifacts),
            "--db",
            str(db_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["quality_gate"]["blocked"] is True


@pytest.mark.slow
@pytest.mark.skipif(not BULK.exists(), reason="2025 bulk is local-only and gitignored")
def test_2025_bulk_full_pipeline(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    artifacts = tmp_path / "artifacts"
    summary = run_pipeline(BULK, settings(tmp_path))

    assert summary["tenders"] == 124_538
    assert summary["cohort_records"] == 59_141
    assert summary["quality_gate"]["blocked"] is False
    assert summary["quality_summary"]["failed_checks"] == 0
    assert summary["mype_opportunities"] > 0
    assert (artifacts / "tenders.parquet").exists()
    verify_checksums(artifacts)
